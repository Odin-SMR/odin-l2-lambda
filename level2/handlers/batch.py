from typing import Any, Dict, List, Literal, NewType

from pydantic import BaseModel, TypeAdapter
from typing_extensions import TypedDict

ODIN_API_ROOT = "https://odin-smr.org"

PROJECT_CONF = {
    21: {
        "tag": "meso21",
        "project": "meso21",
    },
    1: {
        "tag": "stnd1",
        "project": "ALL-Strat-v3.0.0",
    },
    2: {
        "tag": "stnd2",
        "project": "ALL-Strat-v3.0.0",
    },
    8: {
        "tag": "stnd8",
        "project": "ALL-Strat-v3.0.0",
    },
    17: {
        "tag": "stnd17",
        "project": "ALL-Strat-v3.0.0",
    },
    13: {
        "tag": "meso13",
        "project": "ALL-Meso-v3.0.0",
    },
    14: {
        "tag": "meso14",
        "project": "ALL-Meso-v3.0.0",
    },
    19: {
        "tag": "meso19",
        "project": "ALL-Meso-v3.0.0",
    },
    22: {
        "tag": "meso22",
        "project": "ALL-Meso-v3.0.0",
    },
    24: {
        "tag": "meso24",
        "project": "ALL-Meso-v3.0.0",
    },
}


ODIN_API_ROOT = "https://odin-smr.org/rest_api"


class L2_job(TypedDict):
    backend: Literal["AC1", "AC2"]
    freqmode: int
    scanid: int


Batch = NewType("Batch", List[L2_job])


class QSMRJob(BaseModel):
    source: str
    target: str


class QsmrBatch:
    batch: Batch | None = None

    @classmethod
    def from_python(cls, object: object) -> "QsmrBatch":
        batch_adapter = TypeAdapter(Batch)
        raw_batch = batch_adapter.validate_python(object, strict=False)
        return cls(raw_batch)

    def __init__(self, batch: Batch | None):
        self.batch = batch

    def make_batch(self) -> Dict[str, Any]:
        project_batch: Dict[str, Any] = {}
        if self.batch:
            for b in self.batch:
                config = PROJECT_CONF.get(b["freqmode"], None)
                if config:
                    tag = config["tag"]
                    project = config["project"]
                    job_data = self._make_job_data(
                        b["scanid"],
                        b["freqmode"],
                        project,
                        ODIN_API_ROOT,
                    )
                    project_batch.setdefault(tag, []).append(job_data)
        return project_batch

    def _make_job_data(
        self,
        scanid: int,
        freqmode: int,
        project: str,
        api_root: str,
    ) -> dict[str, Any]:
        return QSMRJob(
            source=f"{api_root}/v5/level1/{freqmode}/{scanid}/Log/", target=project
        ).model_dump()


def handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    jobs = QsmrBatch.from_python(event["input"])
    return jobs.make_batch()
