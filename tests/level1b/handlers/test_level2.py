import json
import os
from unittest.mock import patch

import pytest  # type: ignore

from level2.handlers.level2 import (
    get_env_or_raise,
    parse_event_message,
)


@patch.dict(os.environ, {"DEFINITELY": "set"})
def test_get_env_or_raise():
    assert get_env_or_raise("DEFINITELY") == "set"


def test_get_env_or_raise_raises():
    with pytest.raises(
        EnvironmentError,
        match="DEFINITELYNOT is a required environment variable"
    ):
        get_env_or_raise("DEFINITELYNOT")


def test_parse_event_message():
    msg = {
        "Records": [{
            "body": json.dumps({
                "sourceURL": "http://read.data.here/12345",
                "targetURL": "http://post.data.here/12345",
            }),
        }],
    }
    assert parse_event_message(msg) == (
        "http://read.data.here/12345",
        "http://post.data.here/12345",
    )
