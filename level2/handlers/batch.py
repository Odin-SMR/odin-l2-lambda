from typing import Any, Literal, NewType

from pydantic import BaseModel, TypeAdapter
from typing_extensions import TypedDict

from .config import PROJECT_CONF

ODIN_API_ROOT = "https://odin-smr.org/rest_api"


class L2_job(TypedDict):
    backend: Literal["AC1", "AC2"]
    freqmode: int
    scanid: int


Batch = NewType("Batch", list[L2_job])


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

    def make_batch(self) -> dict[str, Any]:
        project_batch: dict[str, Any] = {}
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


def handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    jobs = QsmrBatch.from_python(event["input"])
    return jobs.make_batch()
