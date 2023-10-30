import base64
from io import BytesIO
from json import dumps
from typing import Any, Dict, List, Literal, NewType
from typing_extensions import TypedDict
from Crypto.Cipher import AES
from pydantic import TypeAdapter
from boto3 import client

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
    13: {
        "tag": "meso13",
        "project": "ALL-Meso-v3.0.0",
    },
    19: {
        "tag": "meso19",
        "project": "ALL-Meso-v3.0.0",
    },
}


ODIN_API_ROOT = "https://odin-smr.org/rest_api"
ODIN_API_KEY_NAME = "/odin-api/worker-key"


class L2_job(TypedDict):
    backend: Literal["AC1", "AC2"]
    freqmode: int
    scanid: int


Batch = NewType("Batch", List[L2_job])


class QsmrBatch:
    batch: Batch | None = None

    @classmethod
    def from_python(cls, object: object):
        batch_adapter = TypeAdapter(Batch)
        raw_batch = batch_adapter.validate_python(object, strict=False)
        return cls(raw_batch)

    def __init__(self, batch: Batch | None):
        self.batch = batch

    def make_batch(self, odinapi_password: str) -> Dict[str, Any]:
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
                        odinapi_password,
                    )
                    project_batch.setdefault(tag, []).append(job_data)
        return project_batch

    def _encrypt(self, msg: str, secret: str):
        cipher = AES.new(base64.b64decode(secret.encode()), AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(msg.encode())
        bytes = BytesIO()
        for x in (cipher.nonce, tag, ciphertext):
            bytes.write(x)
        bytes.seek(0)
        return base64.urlsafe_b64encode(bytes.read()).decode("utf8")

    def _encode_level2_target_parameter(
        self,
        scanid: int,
        freqmode: int,
        project: str,
        secret: str,
    ):
        """Return encrypted string from scanid, freqmode and project to be used as
        parameter in a level2 post url
        """
        data = {"ScanID": scanid, "FreqMode": freqmode, "Project": project}
        return self._encrypt(dumps(data), secret)

    def _make_job_data(
        self,
        scanid: int,
        freqmode: int,
        project: str,
        api_root: str,
        api_pass: str,
    ):
        return {
            "source": api_root
            + "/v4/level1/{freqmode}/{scanid}/Log/".format(
                scanid=scanid,
                freqmode=freqmode,
            ),
            "target": api_root
            + "/v5/level2?d={data}".format(
                data=self._encode_level2_target_parameter(
                    scanid,
                    freqmode,
                    project,
                    api_pass,
                ),
            ),
        }


def handler(event: Dict[str, Any], context: Dict[str, Any]):
    ssm_client = client("ssm")
    password = ""
    password_parameter = ssm_client.get_parameter(
        Name=ODIN_API_KEY_NAME,
        WithDecryption=True,
    )["Parameter"]
    if "Value" in password_parameter:
        password = password_parameter["Value"]
    else:
        RuntimeError("No password parameter value")
    jobs = QsmrBatch.from_python(event["input"])
    return jobs.make_batch(password)
