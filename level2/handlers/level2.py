import json
import subprocess
from typing import Any, Dict, Tuple


Event = Dict[str, Any]
Context = Any


def parse_event_message(event: Event) -> Tuple[str, str]:
    message: Dict[str, Any] = json.loads(event["Records"][0]["body"])
    source_url = message["sourceURL"]
    target_url = message["targetURL"]
    return source_url, target_url


def handler(event: Event, context: Context):
    source_url, target_url = parse_event_message(event)

    subprocess.call([
        "/qsmr/run_runscript.sh",
        "/opt/matlab/v90",
        source_url,
        target_url,
    ])
