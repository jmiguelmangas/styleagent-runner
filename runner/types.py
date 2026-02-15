"""Runner job models and transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

JobType = Literal["compile_captureone"]
JobStatus = Literal["picked_up", "running", "succeeded", "failed"]
LogLevel = Literal["info", "error"]

_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    "picked_up": {"running"},
    "running": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
}


@dataclass(frozen=True)
class CompileCaptureOnePayload:
    style_id: str
    version: str


@dataclass(frozen=True)
class Job:
    job_id: str
    job_type: JobType
    payload: CompileCaptureOnePayload
    status: JobStatus = "picked_up"


@dataclass(frozen=True)
class JobLog:
    timestamp: str
    level: LogLevel
    event: str
    job_id: str
    status: JobStatus
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        level: LogLevel,
        event: str,
        job_id: str,
        status: JobStatus,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> "JobLog":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            event=event,
            job_id=job_id,
            status=status,
            message=message,
            context=context or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "event": self.event,
            "job_id": self.job_id,
            "status": self.status,
            "message": self.message,
            "context": self.context,
        }


@dataclass(frozen=True)
class JobExecutionResult:
    job_id: str
    status: JobStatus
    result: dict[str, Any] | None
    error: str | None
    logs: list[JobLog]


def transition_status(current: JobStatus, target: JobStatus) -> JobStatus:
    allowed = _ALLOWED_TRANSITIONS[current]
    if target not in allowed:
        raise ValueError(f"Invalid status transition: {current} -> {target}")
    return target


def job_from_dict(data: dict[str, Any]) -> Job:
    job_id = data.get("job_id")
    job_type = data.get("job_type")
    payload_raw = data.get("payload")

    if not isinstance(job_id, str) or not job_id:
        raise ValueError("Invalid job payload: missing job_id")
    if job_type != "compile_captureone":
        raise ValueError(f"Unsupported job type: {job_type}")
    if not isinstance(payload_raw, dict):
        raise ValueError("Invalid job payload: missing payload object")

    style_id = payload_raw.get("style_id")
    version = payload_raw.get("version")
    if not isinstance(style_id, str) or not isinstance(version, str):
        raise ValueError("Invalid compile_captureone payload")

    status_raw = data.get("status")
    status: JobStatus = "picked_up"
    if status_raw in {"picked_up", "running", "succeeded", "failed"}:
        status = status_raw

    return Job(
        job_id=job_id,
        job_type="compile_captureone",
        payload=CompileCaptureOnePayload(style_id=style_id, version=version),
        status=status,
    )
