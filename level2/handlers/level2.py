import os
import json
import subprocess
from typing import Any, Dict, Tuple

import boto3


Event = Dict[str, Any]
Context = Any


def get_env_or_raise(variable_name: str) -> str:
    if (var := os.environ.get(variable_name)) is None:
        raise EnvironmentError(
            f"{variable_name} is a required environment variable"
        )
    return var


def parse_event_message(event: Event) -> Tuple[str, str]:
    message: Dict[str, Any] = json.loads(event["Records"][0]["body"])
    source_url = message["sourceURL"]
    target_url = message["targetURL"]
    return source_url, target_url


def handler(event: Event, context: Context):
    ssm_client = boto3.client("ssm")

    target_user = get_env_or_raise("ODIN_API_USER")
    target_pass_ssm_name = get_env_or_raise("ODIN_API_KEY_SSM_NAME")

    source_url, target_url = parse_event_message(event)

    target_pass = ssm_client.get_parameter(
        Name=target_pass_ssm_name,
        WithDecryption=True,
    )["Parameter"]["Value"]

    subprocess.call([
        "/qsmr/run_runscript.sh",
        "/opt/matlab/v90",
        source_url,
        target_url,
        target_user,
        target_pass,
    ])
