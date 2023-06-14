from typing import cast, Any
from json import dumps

from aws_cdk import Duration, Stack, RemovalPolicy
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType
from aws_cdk.aws_iam import Effect, PolicyStatement
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.aws_sqs import Queue, DeadLetterQueue
from constructs import Construct


QUEUE_NAME = "OdinSMRLevel2Queue-{project}-{freqmode}"


class Level2JobsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        projects: list[dict[str, Any]],
        odin_api_root: str,
        worker_key_ssm_name: str,
        lambda_timeout: Duration = Duration.seconds(900),
        lambda_schedule: Schedule = Schedule.rate(Duration.days(1)),
        queue_retention_period: Duration = Duration.days(14),
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_name = "OdinSMRLevel2JobsLambda"
        processing_table_name = "OdinSMRLevel2ProcessingTable"

        level2_jobs_lambda = PythonFunction(
            self,
            lambda_name,
            entry="level2",
            handler="handler",
            index="handlers/level2_jobs.py",
            runtime=Runtime.PYTHON_3_9,
            timeout=lambda_timeout,
            environment={
                "ODIN_API_ROOT": odin_api_root,
                "ODIN_API_KEY_SSM_NAME": worker_key_ssm_name,
                "ODIN_LEVEL2_PROCESSING_TABLE": processing_table_name,
            },
        )

        for project_settings in projects:
            clean_project = cast(
                str,
                project_settings["Name"],
            ).replace(".", "-")
            project_settings["JobQueues"] = dict()
            for freqmode, _ in project_settings["FreqModes"].items():
                queue_name = QUEUE_NAME.format(
                    project=clean_project,
                    freqmode=freqmode,
                )

                event_queue = Queue(
                    self,
                    queue_name,
                    queue_name=queue_name,
                    retention_period=queue_retention_period,
                    visibility_timeout=lambda_timeout,
                    removal_policy=RemovalPolicy.RETAIN,
                    dead_letter_queue=DeadLetterQueue(
                        max_receive_count=1,
                        queue=Queue(
                            self,
                            "Failed" + queue_name,
                            retention_period=queue_retention_period,
                        ),
                    ),
                )

                event_queue.grant_send_messages(level2_jobs_lambda)

                project_settings["JobQueues"][freqmode] = {
                    "Name": event_queue.queue_name,
                    "ARN": event_queue.queue_arn,
                }

        # Add project settings here, since JobQueues is constructed above:
        level2_jobs_lambda.add_environment(
            "ODIN_API_L2_PROJECTS",
            dumps(project_settings),
        )

        level2_jobs_lambda.add_to_role_policy(PolicyStatement(
            effect=Effect.ALLOW,
            actions=["ssm:GetParameter"],
            resources=[f"arn:aws:ssm:*:*:parameter{worker_key_ssm_name}"]
        ))

        schedule = Rule(
            self,
            lambda_name + "Schedule",
            schedule=lambda_schedule,
        )

        schedule.add_target(LambdaFunction(level2_jobs_lambda))

        jobs_table = Table(
            self,
            processing_table_name,
            table_name=processing_table_name,
            partition_key=Attribute(name="Project", type=AttributeType.STRING),
        )
        jobs_table.grant_read_write_data(level2_jobs_lambda)

        self.projects = projects
