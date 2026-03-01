"""Backend API helper for runner polling contracts."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from runner.http import RunnerHttpClient
from runner.types import Job, JobExecutionResult, job_from_dict


class RunnerBackendApi:
    def __init__(self, client: RunnerHttpClient) -> None:
        self._client = client

    def get_job(self, job_id: str) -> Job:
        payload = self._client.request_json(
            "GET",
            f"/runner/jobs/{job_id}",
            headers=_trace_headers(action="get-job", job_id=job_id),
        )
        if not isinstance(payload, dict):
            raise ValueError("Invalid job payload from backend")
        return job_from_dict(payload)

    def list_pending_jobs(self, *, limit: int = 1) -> list[Job]:
        payload = self._client.request_json(
            "GET",
            "/runner/jobs",
            params={"status": "pending", "limit": limit},
            headers=_trace_headers(action="list-pending"),
        )

        raw_items: list[dict[str, Any]]
        if isinstance(payload, list):
            raw_items = [item for item in payload if isinstance(item, dict)]
        elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
            raw_items = [item for item in payload["items"] if isinstance(item, dict)]
        else:
            raise ValueError("Invalid jobs payload from backend")

        return [job_from_dict(item) for item in raw_items]

    def claim_job(self, job_id: str) -> None:
        _ = self._client.request_json(
            "POST",
            f"/runner/jobs/{job_id}/claim",
            headers=_trace_headers(action="claim", job_id=job_id),
        )

    def heartbeat_job(self, job_id: str, status: str) -> None:
        _ = self._client.request_json(
            "POST",
            f"/runner/jobs/{job_id}/heartbeat",
            json={"status": status},
            headers=_trace_headers(action="heartbeat", job_id=job_id),
        )

    def complete_job(self, result: JobExecutionResult) -> None:
        payload = {
            "status": result.status,
            "result": result.result,
            "error": result.error,
            "logs": [log.to_dict() for log in result.logs],
        }
        _ = self._client.request_json(
            "POST",
            f"/runner/jobs/{result.job_id}/complete",
            json=payload,
            headers=_trace_headers(action="complete", job_id=result.job_id),
        )


def _trace_headers(*, action: str, job_id: str | None = None) -> dict[str, str]:
    request_id = _build_request_id(action=action, job_id=job_id)
    headers = {"X-Request-ID": request_id}
    if job_id is not None:
        headers["X-Runner-Job-ID"] = job_id
    return headers


def _build_request_id(*, action: str, job_id: str | None = None) -> str:
    suffix = uuid4().hex[:8]
    if job_id:
        return f"runner-{action}-{job_id}-{suffix}"
    return f"runner-{action}-{suffix}"
