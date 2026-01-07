from level2.handlers.batch import QsmrBatch, Batch
import pytest


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
        jobs = batch.make_batch()
        assert len(jobs["stnd1"]) == 1
        assert len(jobs["stnd2"]) == 1
        assert "target" in jobs["stnd1"][0]
        assert "source" in jobs["stnd1"][0]

    def test_batch_empty(self):
        batch = QsmrBatch(Batch([]))
        assert batch.make_batch() == {}

    def test_batch_url(self):
        batch = QsmrBatch.from_python([dict(backend="AC1", freqmode=24, scanid=1001)])
        jobs = batch.make_batch()
        assert jobs["meso24"][0]["source"] == (
            "https://odin-smr.org/rest_api/v5/level1/24/1001/Log/"
        )
        assert jobs["meso24"][0]["target"] == "ALL-Meso-v3.0.0"
