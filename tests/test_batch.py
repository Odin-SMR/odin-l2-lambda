import json
from level2.handlers.batch import QsmrBatch, Batch
import pytest

FAKE_KEY = "01234567890123456789012345678901"


@pytest.fixture
def obj():
    data = [
        dict(backend="AC2", freqmode=1, scanid="1234", extra="faulty"),
        dict(backend="AC1", freqmode=2, scanid=1235),
    ]
    return data


class TestBatch:
    def test_convert_to_int(self, obj):
        batch = QsmrBatch.from_python(obj)
        assert batch.batch
        assert batch.batch[0]["scanid"] == 1234

    def test_convert_all(self, obj):
        batch = QsmrBatch.from_python(obj)
        assert batch.batch
        assert len(batch.batch) == 2

    def test_batches(self, obj):
        batch = QsmrBatch.from_python(obj)
        jobs = batch.make_batch(FAKE_KEY)
        assert len(jobs["stnd1"]) == 1
        assert len(jobs["stnd2"]) == 1
        assert "target" in jobs["stnd1"][0]
        assert "source" in jobs["stnd1"][0]

    def test_batch_empty(self):
        batch = QsmrBatch(Batch([]))
        assert batch.make_batch(FAKE_KEY) == {}
