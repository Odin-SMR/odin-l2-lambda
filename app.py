#!/usr/bin/env python3
from os import makedirs
from typing import cast

from aws_cdk import App

from stacks.level2_stack import Level2Stack

app = App()

# This format mostly follows that of `v5/level2/projects/`, but with the
# addition of `FreqMode` and `InvMode`
projects = [
    {
        "Name": "meso21",
        "URLS": {
            "URL-project": "http://malachite.rss.chalmers.se/rest_api/v5/level2/meso21/",  # noqa: E501
        },
        "FreqMode": [21],
        "InvMode": "meso",
    },
    {
        "Name": "ALL-Strat-v3.0.0",
        "URLS": {
            "URL-project": "http://malachite.rss.chalmers.se/rest_api/v5/level2/ALL-Strat-v3.0.0/",  # noqa: E501
        },
        "FreqMode": [1, 2, 8],
        "InvMode": "stnd",
    },
    {
        "Name": "ALL-Meso-v3.0.0",
        "URLS": {
            "URL-project": "http://malachite.rss.chalmers.se/rest_api/v5/level2/ALL-Meso-v3.0.0/",  # noqa: E501
        },
        "FreqMode": [13, 14, 19, 22, 24],
        "InvMode": "meso",
    },
]

makedirs("dockerfiles", exist_ok=True)

for project in projects:
    clean_project = cast(
        str,
        project["Name"],
    ).replace(".", "-")
    Level2Stack(
        app,
        f"OdinSMRLevel2Stack{clean_project}",
        project_settings=project,
        docker_dir="dockerfiles",
        worker_user="odinopt",
        worker_key_ssm_name="/odin-api/worker-key",
    )

app.synth()
