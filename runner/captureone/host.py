"""Host integration helpers for Capture One desktop app."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any


class HostIntegrationError(RuntimeError):
    def __init__(self, *, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_host_integration(self) -> dict[str, Any]:
        return {
            "mode": "host",
            "error_code": self.code,
            "error_message": self.message,
            **({"error_details": self.details} if self.details else {}),
        }

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def ensure_captureone_app_exists(app_path: str) -> Path:
    path = Path(app_path).expanduser()
    if not path.exists():
        raise HostIntegrationError(
            code="APP_NOT_INSTALLED",
            message=f"Capture One app not found: {path}",
            details={"captureone_app_path": str(path)},
        )
    return path


def build_import_output_path(import_dir: str, artifact_id: str) -> Path:
    directory = Path(import_dir).expanduser()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HostIntegrationError(
            code="IMPORT_DIR_NOT_WRITABLE",
            message=f"Cannot create import directory: {directory}",
            details={"import_dir": str(directory), "os_error": str(exc)},
        ) from exc
    return directory / f"{artifact_id}.costyle"


def open_costyle_in_captureone(
    *,
    app_path: str,
    costyle_path: Path,
    timeout_seconds: float,
) -> None:
    try:
        subprocess.run(
            ["open", "-a", app_path, str(costyle_path)],
            check=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise HostIntegrationError(
            code="OPEN_TIMEOUT",
            message="Timed out while opening .costyle in Capture One",
            details={"timeout_seconds": timeout_seconds, "costyle_path": str(costyle_path)},
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HostIntegrationError(
            code="APPLE_EVENT_DENIED",
            message="Capture One open command failed. Check Automation permissions.",
            details={"returncode": exc.returncode, "costyle_path": str(costyle_path)},
        ) from exc
