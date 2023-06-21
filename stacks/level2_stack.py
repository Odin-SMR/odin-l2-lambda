from typing import cast, Any
from warnings import warn

from aws_cdk import Duration, Stack
from aws_cdk.aws_lambda import (
    Architecture,
    DockerImageCode,
    DockerImageFunction,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_sqs import Queue
from constructs import Construct

from .level2_jobs_stack import QUEUE_NAME


DOCKER_IMAGE = """
FROM public.ecr.aws/lambda/python:3.9

# Copy Matlab runtime and QSMR
COPY --from=odinsmr/u-jobs:{tag} /opt/matlab /opt/matlab
COPY --from=odinsmr/u-jobs:{tag} /qsmr /qsmr
COPY --from=odinsmr/u-jobs:{tag} /QsmrData /QsmrData
ENV LD_LIBRARY_PATH=/opt/matlab/v90/runtime/glnxa64:/opt/matlab/v90/bin/glnxa64:/opt/matlab/v90/sys/os/glnxa64:$LD_LIBRARY_PATH

# Copy function code
COPY ./level2/handlers/level2.py /var/task

# Set the CMD to handler
CMD [ "level2.lambda_handler" ]
"""  # noqa: E501


class Level2Stack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        project_settings: dict[str, Any],
        docker_dir: str,
        lambda_timeout: Duration = Duration.seconds(900),
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_name = "OdinSMRLevel2Lambda-{project}-{freqmode}"
        docker_name = "Dockerfile-{tag}"
        clean_project = cast(
            str,
            project_settings["Name"],
        ).replace(".", "-")

        for freqmode, tag in project_settings["FreqModes"].items():
            if tag is None:
                warn(
                    f"No tag for {project_settings['Name']} for FM {freqmode}."
                )
                continue
            docker_file = docker_dir + "/" + docker_name.format(tag=tag)
            with open(docker_file, "w") as fp:
                fp.write(DOCKER_IMAGE.format(tag=tag))
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
                memory_size=6144,
            )

            queue_name = QUEUE_NAME.format(
                project=clean_project,
                freqmode=freqmode,
            )
            event_queue = Queue.from_queue_arn(
                self,
                queue_name,
                project_settings["JobQueues"][freqmode]["ARN"]
            )

            level2_lambda.add_event_source(SqsEventSource(
                event_queue,
                batch_size=1,
            ))
