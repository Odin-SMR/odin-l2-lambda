import base64
import os
from datetime import datetime, timedelta
from io import BytesIO
from json import dumps, loads
from typing import Any, Dict, Iterator, List, NamedTuple
from warnings import warn

import boto3
import requests
from botocore.exceptions import ClientError
from Crypto.Cipher import AES


BotoClient = Any
BotoResource = Any
SSMClient = Any
SQSClient = Any
DbResource = Any
Table = Any
Context = Any
Event = Dict[str, Any]
Project = Dict[str, Any]

DEFAULT_START = datetime(2022, 12, 29)


class AddJobError(Exception):
    pass


class Job(NamedTuple):
    scan_id: int
    timestamp: datetime = DEFAULT_START


def get_env_or_raise(variable_name: str) -> str:
    if (var := os.environ.get(variable_name)) is None:
        raise EnvironmentError(
            f"{variable_name} is a required environment variable"
        )
    return var


def get_latest_job(
    project: str,
    freqmode: int,
    table: Table,
) -> Job:
    try:
        item = table.get_item(
            Key={"Project": project, "Freqmode": freqmode},
        )["Item"]
        return Job(
            int(item["ScanID"]),
            datetime.fromisoformat(item["Timestamp"]),
        )
    except ClientError:
        return Job(-1, DEFAULT_START)


def put_latest_job(
    job: Job,
    project: str,
    freqmode: int,
    table: BotoResource,
):
    item = {
        "Project": project,
        "FreqMode": freqmode,
        "ScanID": job.scan_id,
        "Timestamp": job.timestamp.isoformat(),
    },
    table.put_item(
        Item=item,
    )


def get_days_with_scans(
    freqmode: int,
    start_day: datetime,
    end_day: datetime,
    api_root: str,
    step_size: int = 365,
) -> Iterator[str]:
    """Get all days between two dates with scans in the specified freqmode.
    """

    while start_day < end_day:
        resp = requests.get(
            api_root + (
                '/v5/period_info/{year}/{month:0>2}/{day:0>2}/'
                '?length={nrdays}'
            ).format(
                year=start_day.year,
                month=start_day.month,
                day=start_day.day,
                nrdays=step_size,
            )
        )
        assert resp.status_code == 200
        data = resp.json()
        days = [
            day['URL']
            for day in data['Data']
            if day['FreqMode'] == freqmode
            and datetime.strptime(day['Date'], '%Y-%m-%d') < end_day
        ]
        for day in sorted(days):
            yield day
        start_day = (
            datetime.strptime(data['PeriodEnd'], '%Y-%m-%d')
            + timedelta(days=1)
        )


def get_jobs_from_log(url: str) -> List[Job]:
    """Return list of scan ids found in url"""
    resp = requests.get(url)
    return [
        Job(int(scan['ScanID']), datetime.fromisoformat(scan["DateTime"]))
        for scan in resp.json()['Data']
    ]


def generate_jobs(
    freqmode: int,
    start_day: datetime,
    end_day: datetime,
    api_root: str,
) -> Iterator[Job]:
    """Generate all scan ids for a freqmode between two dates.
    """

    for url in get_days_with_scans(freqmode, start_day, end_day, api_root):
        for job in get_jobs_from_log(url):
            yield job


def encrypt(msg, secret):
    cipher = AES.new(base64.b64decode(secret.encode()), AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(msg.encode())
    bytes = BytesIO()
    for x in (cipher.nonce, tag, ciphertext):
        bytes.write(x)
    bytes.seek(0)
    return base64.urlsafe_b64encode(bytes.read()).decode('utf8')


def encode_level2_target_parameter(
    scanid: int,
    freqmode: int,
    project: str,
    secret: str,
):
    """Return encrypted string from scanid, freqmode and project to be used as
    parameter in a level2 post url
    """
    data = {'ScanID': scanid, 'FreqMode': freqmode, 'Project': project}
    return encrypt(dumps(data), secret)


def make_job_data(
    scanid: int,
    freqmode: int,
    project: str,
    api_root: str,
    api_pass: str,
):
    return {
        'source_url': api_root + '/v4/l1_log/{freqmode}/{scanid}/'.format(
            scanid=scanid,
            freqmode=freqmode,
        ),
        'target_url': api_root + '/v5/level2?d={data}'.format(
            data=encode_level2_target_parameter(
                scanid,
                freqmode,
                project,
                api_pass,
            ),
        ),
    }


def add_jobs(
    jobs: List[Job],
    freqmode: int,
    project: str,
    queue_name: str,
    api_root: str,
    api_pass: str,
    sqs_client: SQSClient,
) -> Job:
    latest_job = jobs[0]
    for job in jobs:
        if latest_job[1] < job[1]:
            latest_job = job
        job_data = make_job_data(
            scanid=job.scan_id,
            freqmode=freqmode,
            project=project,
            api_root=api_root,
            api_pass=api_pass,
        )
        response = sqs_client.send_message(
            QueueUrl=queue_name,
            MessageBody=dumps(job_data),
            MessageGroupId="OdinLevel2Job",
        )
        if response["ResponseMetadata"]["HttpStatusCode"] != 200:
            raise AddJobError(f"Could not add job {job_data}")
    return latest_job


def handler(event: Event, context: Context):
    api_root = get_env_or_raise("ODIN_API_ROOT")
    api_pass_ssm_name = get_env_or_raise("ODIN_API_KEY_SSM_NAME")
    projects: List[Project] = loads(get_env_or_raise("ODIN_API_L2_PROJECTS"))
    db_name = loads(get_env_or_raise("ODIN_API_L2_PROCESSING_TABLE"))

    ssm_client: SSMClient = boto3.client("ssm")
    sqs_client: SQSClient = boto3.client("sqs")
    dynamodb: DbResource = boto3.resource("dynamodb")

    jobs_table: Table = dynamodb.Table(db_name)

    api_pass = ssm_client.get_parameter(
        Name=api_pass_ssm_name,
        WithDecryption=True,
    )["Parameter"]["Value"]

    resp = requests.get(api_root + '/v5/config_data/latest_ecmf_file')
    latest_ecmf_date = datetime.strptime(resp.json()["Date"], '%Y-%m-%d')

    for project_settings in projects:
        project_name = project_settings["Name"]
        for freqmode, queue in project_settings["JobQueues"].items():
            latest_job = get_latest_job(project_name, freqmode, jobs_table)
            jobs = list(generate_jobs(
                freqmode=freqmode,
                start_day=latest_job.timestamp,
                end_day=latest_ecmf_date,
                api_root=api_root,
            ))
            try:
                latest_job = add_jobs(
                    jobs=jobs,
                    freqmode=freqmode,
                    project=project_name,
                    queue_name=queue["Name"],
                    api_root=api_root,
                    api_pass=api_pass,
                    sqs_client=sqs_client,
                )
                put_latest_job(latest_job, project_name, freqmode, jobs_table)
            except AddJobError as err:
                warn(f"Could not add jobs to {queue}: {err}")
