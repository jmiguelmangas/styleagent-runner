from runner.poller import RunnerPoller
from runner.types import CompileCaptureOnePayload, Job, JobExecutionResult, JobLog


class FakeApi:
    def __init__(self, jobs: list[Job]) -> None:
        self._jobs = jobs
        self.claimed: list[str] = []
        self.heartbeats: list[tuple[str, str]] = []
        self.completed: list[JobExecutionResult] = []

    def list_pending_jobs(self, *, limit: int = 1) -> list[Job]:
        if not self._jobs:
            return []
        return [self._jobs.pop(0)][:limit]

    def claim_job(self, job_id: str) -> None:
        self.claimed.append(job_id)

    def get_job(self, job_id: str) -> Job:
        for job in self._jobs:
            if job.job_id == job_id:
                return job
        raise ValueError("job not found")

    def heartbeat_job(self, job_id: str, status: str) -> None:
        self.heartbeats.append((job_id, status))

    def complete_job(self, result: JobExecutionResult) -> None:
        self.completed.append(result)


class FakeExecutor:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, job: Job) -> JobExecutionResult:
        self.executed.append(job.job_id)
        return JobExecutionResult(
            job_id=job.job_id,
            status="succeeded",
            result={"ok": True},
            error=None,
            logs=[
                JobLog.create(
                    level="info",
                    event="job_succeeded",
                    job_id=job.job_id,
                    status="succeeded",
                    message="done",
                )
            ],
        )


def test_poller_poll_once_no_jobs_returns_none() -> None:
    api = FakeApi(jobs=[])
    executor = FakeExecutor()
    emitted: list[str] = []
    poller = RunnerPoller(
        api,
        executor,
        poll_interval_seconds=0.01,
        sleep=lambda _: None,
        emit=emitted.append,
    )

    result = poller.poll_once()

    assert result is None
    assert executor.executed == []
    assert emitted == []


def test_poller_poll_once_processes_one_job() -> None:
    api = FakeApi(
        jobs=[
            Job(
                job_id="job_1",
                job_type="compile_captureone",
                payload=CompileCaptureOnePayload(style_id="s1", version="v1"),
            )
        ]
    )
    executor = FakeExecutor()
    emitted: list[str] = []
    poller = RunnerPoller(
        api,
        executor,
        poll_interval_seconds=0.01,
        sleep=lambda _: None,
        emit=emitted.append,
    )

    result = poller.poll_once()

    assert result is not None
    assert result.status == "succeeded"
    assert executor.executed == ["job_1"]
    assert api.claimed == ["job_1"]
    assert api.heartbeats == [("job_1", "running")]
    assert len(api.completed) == 1
    assert len(emitted) == 1


def test_poller_run_job_id_processes_specific_job() -> None:
    api = FakeApi(
        jobs=[
            Job(
                job_id="job_9",
                job_type="compile_captureone",
                payload=CompileCaptureOnePayload(style_id="s9", version="v9"),
            )
        ]
    )
    executor = FakeExecutor()
    emitted: list[str] = []
    poller = RunnerPoller(
        api,
        executor,
        poll_interval_seconds=0.01,
        sleep=lambda _: None,
        emit=emitted.append,
    )

    result = poller.run_job_id("job_9")

    assert result.status == "succeeded"
    assert executor.executed == ["job_9"]
    assert api.claimed == ["job_9"]
    assert api.heartbeats == [("job_9", "running")]
    assert len(api.completed) == 1
    assert len(emitted) == 1
