"""Backend API helper for runner polling contracts."""

from __future__ import annotations

from typing import Any

from runner.http import RunnerHttpClient
from runner.types import Job, JobExecutionResult, job_from_dict


class RunnerBackendApi:
    def __init__(self, client: RunnerHttpClient) -> None:
        self._client = client

    def list_pending_jobs(self, *, limit: int = 1) -> list[Job]:
        payload = self._client.request_json(
            "GET",
            "/runner/jobs",
            params={"status": "pending", "limit": limit},
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
        _ = self._client.request_json("POST", f"/runner/jobs/{job_id}/claim")

    def heartbeat_job(self, job_id: str, status: str) -> None:
        _ = self._client.request_json(
            "POST",
            f"/runner/jobs/{job_id}/heartbeat",
            json={"status": status},
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
        )

