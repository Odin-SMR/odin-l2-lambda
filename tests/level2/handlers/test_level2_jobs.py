import os
from unittest.mock import patch

import pytest  # type: ignore

from level2.handlers.level2_jobs import (
    get_env_or_raise,
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
