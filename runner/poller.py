"""Polling loop for one-job-at-a-time runner execution."""

from __future__ import annotations

from collections.abc import Callable
import json
import time

from runner.api import RunnerBackendApi
from runner.jobs import JobExecutor
from runner.types import Job, JobExecutionResult


class RunnerPoller:
    def __init__(
        self,
        api: RunnerBackendApi,
        executor: JobExecutor,
        *,
        poll_interval_seconds: float,
        sleep: Callable[[float], None] = time.sleep,
        emit: Callable[[str], None] = print,
    ) -> None:
        self._api = api
        self._executor = executor
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep = sleep
        self._emit = emit

    def poll_once(self) -> JobExecutionResult | None:
        jobs = self._api.list_pending_jobs(limit=1)
        if not jobs:
            return None

        return self.execute_job(jobs[0])

    def run_job_id(self, job_id: str) -> JobExecutionResult:
        job = self._api.get_job(job_id)
        return self.execute_job(job)

    def execute_job(self, job: Job) -> JobExecutionResult:
        self._api.claim_job(job.job_id)
        self._api.heartbeat_job(job.job_id, status="running")
        result = self._executor.execute(job)
        self._api.complete_job(result)
        for log in result.logs:
            self._emit(json.dumps(log.to_dict(), sort_keys=True))
        return result

    def poll_forever(self) -> None:
        while True:
            self.poll_once()
            self._sleep(self._poll_interval_seconds)
