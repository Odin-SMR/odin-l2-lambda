from json import dumps
from aws_cdk import BundlingOptions, RemovalPolicy, Stack, Duration
from boto3 import client
from constructs import Construct
from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ssm as ssm,
    aws_logs as logs,
)
from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_ssm import StringParameter
from aws_cdk.aws_sqs import Queue, DeadLetterQueue
from aws_cdk.aws_ecs_patterns import QueueProcessingFargateService

ODIN_API_KEY_NAME = "/odin-api/worker-key"


class EcsStepFunctionStack(Stack):
    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, "OdinECRStack", **kwargs)

        batch_lambda = Function(
            self,
            "BatchLambda",
            runtime=Runtime.PYTHON_3_11,
            code=Code.from_asset(
                "level2",
                bundling=BundlingOptions(
                    image=Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            timeout=Duration.seconds(10),
            function_name=self.__class__.__name__,
            handler="handlers.batch.handler",
            environment={
                "ODIN_API_KEY_SSM_NAME": ODIN_API_KEY_NAME,
            },
        )
        batch_invoke = sfn_tasks.LambdaInvoke(
            self,
            "BatchInvoke",
            lambda_function=batch_lambda,
            input_path="$.l2_job",
            payload=sfn.TaskInput.from_object({"input": sfn.JsonPath.object_at("$")}),
            result_path="$.Batches",
            output_path="$.Batches.Payload",
        )
        vpc = ec2.Vpc.from_lookup(
            self,
            "OsmrVPC",
            is_default=False,
            vpc_name="OdinVPC",
        )
        cluster = ecs.Cluster.from_cluster_attributes(
            self,
            "QsmrCluster",
            cluster_name="OdinApiCluster",
            vpc=vpc,
            security_groups=[],
        )
        parallel_state = sfn.Parallel(self, "RunAllJobs")

        repository = ecr.Repository.from_repository_name(self, "QsmrRepository", "qsmr")
        tags = self.list_ecr_tags(repository.repository_name)
        log_group = logs.LogGroup(
            self,
            "QdinQSMRLogGroup",
            log_group_name="/Odin/QSMR",
            removal_policy=RemovalPolicy.DESTROY,
            retention=RetentionDays.ONE_MONTH,
        )
        for tag in tags:
            success = sfn.Succeed(
                self,
                f"Success{tag}",
                state_name=f"NO {tag} jobs",
                input_path=sfn.JsonPath.DISCARD,
                output_path=sfn.JsonPath.DISCARD,
            )
            dlq = Queue(self, f"QSMRDlq{tag}", queue_name=f"QSMRDlq-{tag}")
            queue = Queue(
                self,
                f"QSMRQueue{tag}",
                dead_letter_queue=DeadLetterQueue(max_receive_count=3, queue=dlq),
                queue_name=f"QSMRQueue-{tag}",
            )

            QueueProcessingFargateService(
                self,
                f"QSMRService{tag}",
                cluster=cluster,
                image=ecs.ContainerImage.from_ecr_repository(repository, tag=tag),
                container_name=f"QSMR{tag}",
                log_driver=ecs.AwsLogDriver(
                    stream_prefix=f"QSMR-{tag}",
                    log_group=log_group,
                ),
                enable_logging=True,
                capacity_provider_strategies=[
                    ecs.CapacityProviderStrategy(
                        capacity_provider="FARGATE_SPOT", weight=1, base=0
                    )
                ],
                family=f"QSMR-{tag}",
                cpu=2048,
                memory_limit_mib=4096,
                min_scaling_capacity=0,
                max_scaling_capacity=10,
                queue=queue,
                service_name=f"QSMR-{tag}",
            )

            map_state = sfn.Map(
                self,
                f"QSMRMap{tag}",
                state_name=f"Queque {tag}",
                input_path=f"$.{tag}",
                items_path="$",
            )
            send_task = sfn_tasks.SqsSendMessage(
                self,
                f"QSMRSendmessage{tag}",
                message_body=sfn.TaskInput.from_json_path_at("$"),
                state_name=f"Queue job {tag}",
                queue=queue,
                result_selector={
                    "request_id": sfn.JsonPath.string_at(
                        "$.SdkResponseMetadata.RequestId"
                    )
                },
                result_path="$.SendRequest",
                output_path="$.SendRequest.request_id",
            )
            map_state.iterator(send_task)
            choice = sfn.Choice(
                self, f"QsmrSplitJob{tag}", state_name=f"Job selector {tag}"
            )
            choice.when(
                sfn.Condition.is_present(f"$.{tag}"),
                map_state,
            ).otherwise(success)
            parallel_state.branch(choice)

        odin_password = StringParameter.from_secure_string_parameter_attributes(
            self, "OdinAPIKey", parameter_name=ODIN_API_KEY_NAME
        )
        odin_password.grant_read(batch_lambda)

        batch_invoke.next(parallel_state)
        sfn.StateMachine(
            self, "StateMachine", definition=batch_invoke, state_machine_name="OdinQSMR"
        )

    def list_ecr_tags(self, repository_name: str) -> list[str]:
        ecr_client = client("ecr")
        tags = []

        paginator = ecr_client.get_paginator("list_images")
        response_iterator = paginator.paginate(
            repositoryName=repository_name,
            filter={"tagStatus": "TAGGED"},
        )

        for response in response_iterator:
            for image in response["imageIds"]:
                if "imageTag" in image:
                    tags.append(image["imageTag"])

        return tags
