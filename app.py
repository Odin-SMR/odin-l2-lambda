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
        "FreqModes": {
            21: "qsmr_meso_21_MESO21ALL20191110_191110",
        },
    },
    {
        "Name": "ALL-Strat-v3.0.0",
        "URLS": {
            "URL-project": "http://malachite.rss.chalmers.se/rest_api/v5/level2/ALL-Strat-v3.0.0/",  # noqa: E501
        },
        "FreqModes": {
            1: "qsmr_stnd_1_ALLSTND1_190830",
            2: "qsmr_stnd_2_Stnd2IncreasedTgridRes_191129",
            8: "qsmr_stnd_8_ALLSTND8_190830",
        },
    },
    {
        "Name": "ALL-Meso-v3.0.0",
        "URLS": {
            "URL-project": "http://malachite.rss.chalmers.se/rest_api/v5/level2/ALL-Meso-v3.0.0/",  # noqa: E501
        },
        "FreqModes": {
            13: "qsmr_stnd_1_ALLSTND1_190830",
            14: None,
            19: "qsmr_meso_19_MESO19SB110ALL19lowTunc2_200306",
            22: None,
            24: None,
        },
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
