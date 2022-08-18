import boto3
from botocore.client import BaseClient

from dstack.aws import logs, artifacts, jobs, run_names, runs, runners, tags, repos, secrets, config
from dstack.backend import *
from dstack.config import AwsBackendConfig


class AwsBackend(Backend):
    def __init__(self, backend_config: AwsBackendConfig):
        self.backend_config = backend_config

    def _s3_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("s3")

    def _ec2_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("ec2")

    def _iam_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("iam")

    def _logs_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("logs")

    def _secretsmanager_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("secretsmanager")

    def _sts_client(self) -> BaseClient:
        session = boto3.Session(profile_name=self.backend_config.profile_name,
                                region_name=self.backend_config.region_name)
        return session.client("sts")

    def configure(self, silent: bool):
        config.configure(self._iam_client(), self._s3_client(), self.backend_config.bucket_name,
                         self.backend_config.region_name, silent)

    def create_run(self, repo_user_name: str, repo_name: str) -> str:
        return runs.create_run(self._s3_client(), self._logs_client(), self.backend_config.bucket_name,
                               repo_user_name, repo_name)

    def submit_job(self, job: Job, counter: List[int]):
        jobs.create_job(self._s3_client(), self.backend_config.bucket_name, job, counter)
        runners.run_job(self._ec2_client(), self._iam_client(), self._s3_client(), self.backend_config.bucket_name,
                        self.backend_config.region_name, job)

    def get_job(self, repo_user_name: str, repo_name: str, job_id: str) -> Job:
        return jobs.get_job(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name, job_id)

    def list_job_heads(self, repo_user_name: str, repo_name: str, run_name: Optional[str] = None):
        return jobs.list_job_heads(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name,
                                   run_name)

    def run_job(self, job: Job) -> Runner:
        return runners.run_job(self._ec2_client(), self._iam_client(), self._s3_client(),
                               self.backend_config.bucket_name, self.backend_config.region_name, job)

    def stop_job(self, repo_user_name: str, repo_name: str, job_id: str, abort: bool):
        job = self.get_job(repo_user_name, repo_name, job_id)
        runners.stop_job(self._ec2_client(), self._s3_client(), self.backend_config.bucket_name, job, abort)

    def delete_job_head(self, repo_user_name: str, repo_name: str, job_id: str):
        jobs.delete_job_head(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name, job_id)

    def list_runs(self, repo_user_name: str, repo_name: str, run_name: Optional[str] = None,
                  include_request_heads: bool = True) -> List[Run]:
        return runs.list_runs(self._ec2_client(), self._s3_client(), self.backend_config.bucket_name, repo_user_name,
                              repo_name, run_name, include_request_heads)

    def get_runs(self, repo_user_name: str, repo_name: str, job_heads: List[JobHead],
                 include_request_heads: bool = True) -> List[Run]:
        return runs.get_runs(self._ec2_client(), self._s3_client(), self.backend_config.bucket_name, repo_user_name,
                             repo_name, job_heads, include_request_heads)

    def poll_logs(self, repo_user_name: str, repo_name: str, job_heads: List[JobHead], start_time: int,
                  attached: bool) -> Generator[LogEvent, None, None]:
        return logs.poll_logs(self._ec2_client(), self._s3_client(), self._logs_client(),
                              self.backend_config.bucket_name, repo_user_name, repo_name, job_heads, start_time,
                              attached)

    def list_run_artifact_files(self, repo_user_name: str, repo_name: str, run_name: str) -> List[Tuple[str, str, int]]:
        return artifacts.list_run_artifact_files(self._s3_client(), self.backend_config.bucket_name,
                                                 repo_user_name, repo_name, run_name)

    def download_run_artifact_files(self, repo_user_name: str, repo_name: str, run_name: str,
                                    output_dir: Optional[str]):
        artifacts.download_run_artifact_files(self._s3_client(), self.backend_config.bucket_name,
                                              repo_user_name, repo_name, run_name, output_dir)

    def list_tag_heads(self, repo_user_name: str, repo_name: str) -> List[TagHead]:
        return tags.list_tag_heads(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name)

    def get_tag_head(self, repo_user_name: str, repo_name: str, tag_name: str) -> Optional[TagHead]:
        return tags.get_tag_head(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name,
                                 tag_name)

    def create_tag_from_run(self, repo_user_name: str, repo_name: str, tag_name: str, run_name: str):
        tags.create_tag_from_run(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name,
                                 tag_name, run_name)

    def delete_tag(self, repo_user_name: str, repo_name: str, tag_head: TagHead):
        tags.delete_tag(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name, tag_head)

    def create_tag_from_local_dirs(self, repo_data: RepoData, tag_name: str, local_dirs: List[str]):
        tags.create_tag_from_local_dirs(self._s3_client(), self._logs_client(), self.backend_config.bucket_name,
                                        repo_data, tag_name, local_dirs)

    def list_repo_heads(self) -> List[RepoHead]:
        return repos.list_repo_heads(self._s3_client(), self.backend_config.bucket_name)

    def update_repo_last_run_at(self, repo_user_name: str, repo_name: str, last_run_at: int):
        repos.update_repo_last_run_at(self._s3_client(), self.backend_config.bucket_name, repo_user_name, repo_name,
                                      last_run_at)

    def increment_repo_tags_count(self, repo_user_name: str, repo_name: str):
        repos.increment_repo_tags_count(self._s3_client(), self.backend_config.bucket_name, repo_user_name,
                                        repo_name)

    def decrement_repo_tags_count(self, repo_user_name: str, repo_name: str):
        repos.decrement_repo_tags_count(self._s3_client(), self.backend_config.bucket_name, repo_user_name,
                                        repo_name)

    def save_repo_credentials(self, repo_user_name: str, repo_name: str, repo_credentials: RepoCredentials):
        repos.save_repo_credentials(self._sts_client(), self._iam_client(), self._secretsmanager_client(),
                                    self.backend_config.bucket_name, repo_user_name, repo_name, repo_credentials)

    def list_run_artifact_objects(self, repo_user_name: str, repo_name: str, job_id: str,
                                  path: str) -> List[Tuple[str, bool]]:
        return artifacts.list_run_artifact_objects(self._s3_client(), self.backend_config.bucket_name, repo_user_name,
                                                   repo_name, job_id, path)

    def list_secret_names(self) -> List[str]:
        return secrets.list_secret_names(self._secretsmanager_client(), self.backend_config.bucket_name)

    def get_secret(self, secret_name: str) -> Optional[Secret]:
        return secrets.get_secret(self._secretsmanager_client(), self.backend_config.bucket_name, secret_name)

    def add_secret(self, secret: Secret):
        return secrets.add_secret(self._sts_client(), self._iam_client(), self._secretsmanager_client(),
                                  self.backend_config.bucket_name, secret)

    def update_secret(self, secret: Secret):
        return secrets.update_secret(self._secretsmanager_client(), self.backend_config.bucket_name, secret)

    def delete_secret(self, secret_name: str):
        return secrets.delete_secret(self._secretsmanager_client(), self.backend_config.bucket_name, secret_name)
