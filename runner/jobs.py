"""Job dispatcher and execution flow."""

from __future__ import annotations

from typing import Any

from runner.captureone.compile import run_compile_captureone
from runner.http import RunnerHttpClient
from runner.types import Job, JobExecutionResult, JobLog, transition_status


class JobExecutor:
    """Execute a single job at a time (MVP, no concurrency)."""

    def __init__(self, client: RunnerHttpClient) -> None:
        self._client = client

    def execute(self, job: Job) -> JobExecutionResult:
        logs: list[JobLog] = []
        current_status = job.status
        result: dict[str, Any] | None = None
        error: str | None = None

        logs.append(
            JobLog.create(
                level="info",
                event="job_picked_up",
                job_id=job.job_id,
                status=current_status,
                message=f"Picked up job type={job.job_type}",
            )
        )

        current_status = transition_status(current_status, "running")
        logs.append(
            JobLog.create(
                level="info",
                event="job_running",
                job_id=job.job_id,
                status=current_status,
                message="Job execution started",
            )
        )

        try:
            if job.job_type == "compile_captureone":
                result = run_compile_captureone(self._client, job.payload)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")

            current_status = transition_status(current_status, "succeeded")
            logs.append(
                JobLog.create(
                    level="info",
                    event="job_succeeded",
                    job_id=job.job_id,
                    status=current_status,
                    message="Job execution completed",
                    context={"result": result},
                )
            )
        except Exception as exc:
            error = str(exc)
            current_status = transition_status(current_status, "failed")
            logs.append(
                JobLog.create(
                    level="error",
                    event="job_failed",
                    job_id=job.job_id,
                    status=current_status,
                    message="Job execution failed",
                    context={"error": error},
                )
            )

        return JobExecutionResult(
            job_id=job.job_id,
            status=current_status,
            result=result,
            error=error,
            logs=logs,
        )

