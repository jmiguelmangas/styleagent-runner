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

