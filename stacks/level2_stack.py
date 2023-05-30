from typing import cast, Any

from aws_cdk import Duration, Stack, RemovalPolicy
from aws_cdk.aws_iam import Effect, PolicyStatement
from aws_cdk.aws_lambda import (
    Architecture,
    DockerImageCode,
    DockerImageFunction,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_sqs import DeadLetterQueue, Queue
from constructs import Construct

DOCKER_IMAGE = """

FROM public.ecr.aws/lambda/python:3.9
# Copy Matlab runtime and QSMR
COPY --from=odinsmr/u-jobs:qsmr_{invmode}_{freqmode}_{project} /opt/matlab /opt/matlab
COPY --from=odinsmr/u-jobs:qsmr_{invmode}_{freqmode}_{project} /qsmr /qsmr

# Copy function code
COPY ./level2/handlers/level2.py /var/task

# Set the CMD to handler
CMD [ "level2.lambda_handler" ]
"""


class Level2Stack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        project_settings: dict[str, Any],
        docker_dir: str,
        worker_user: str,
        worker_key_ssm_name: str,
        lambda_timeout: Duration = Duration.seconds(900),
        queue_retention_period: Duration = Duration.days(14),
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_name = "OdinSMRLevel2Lambda-{project}-{freqmode}"
        queue_name = "OdinSMRLevel2Queue-{project}-{freqmode}"
        docker_name = "Dockerfile-{project}-{freqmode}"
        clean_project = cast(
            str,
            project_settings["Name"],
        ).replace(".", "-")

        for freqmode in project_settings["FreqMode"]:
            docker_file = docker_dir + "/" + docker_name.format(
                project=project_settings["Name"],
                freqmode=freqmode,
            )
            with open(docker_file, "w") as fp:
                fp.write(DOCKER_IMAGE.format(
                    project=project_settings["Name"],
                    freqmode=freqmode,
                    invmode=project_settings["InvMode"],
                ))
            level2_lambda = DockerImageFunction(
                self,
                lambda_name.format(
                    project=clean_project,
                    freqmode=freqmode,
                ),
                code=DockerImageCode.from_image_asset(
                    ".",
                    file=docker_file,
                ),
                timeout=lambda_timeout,
                architecture=Architecture.X86_64,
                memory_size=4096,
                environment={
                    "ODIN_API_USER": worker_user,
                    "ODIN_API_KEY_SSM_NAME": worker_key_ssm_name,
                },
            )

            event_queue = Queue(
                self,
                queue_name.format(
                    project=clean_project,
                    freqmode=freqmode,
                ),
                retention_period=queue_retention_period,
                visibility_timeout=lambda_timeout,
                removal_policy=RemovalPolicy.RETAIN,
                dead_letter_queue=DeadLetterQueue(
                    max_receive_count=1,
                    queue=Queue(
                        self,
                        "Failed" + queue_name.format(
                            project=clean_project,
                            freqmode=freqmode,
                        ),
                        retention_period=queue_retention_period,
                    ),
                ),
            )

            level2_lambda.add_event_source(SqsEventSource(
                event_queue,
                batch_size=1,
            ))
            level2_lambda.add_to_role_policy(PolicyStatement(
                effect=Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:*:*:parameter{worker_key_ssm_name}"]
            ))
