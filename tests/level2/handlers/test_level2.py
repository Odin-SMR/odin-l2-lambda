import json

from level2.handlers.level2 import (
    parse_event_message,
)


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
