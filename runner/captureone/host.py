"""Host integration helpers for Capture One desktop app."""

from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any, Literal


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


def _run_cli_import(
    *,
    command_template: str,
    app_path: str,
    costyle_path: Path,
    timeout_seconds: float,
) -> None:
    if not command_template.strip():
        raise HostIntegrationError(
            code="APP_NOT_INSTALLED",
            message="Capture One CLI command is required when launch mode is cli.",
            details={"hint": "Set RUNNER_CAPTUREONE_CLI_COMMAND"},
        )

    try:
        command = shlex.split(command_template.format(app_path=app_path, costyle_path=str(costyle_path)))
    except Exception as exc:
        raise HostIntegrationError(
            code="APPLE_EVENT_DENIED",
            message="Invalid Capture One CLI command template.",
            details={"command_template": command_template, "error": str(exc)},
        ) from exc

    if not command:
        raise HostIntegrationError(
            code="APPLE_EVENT_DENIED",
            message="Capture One CLI command template resolved to an empty command.",
        )

    try:
        subprocess.run(command, check=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        raise HostIntegrationError(
            code="OPEN_TIMEOUT",
            message="Timed out while importing .costyle using Capture One CLI command",
            details={"timeout_seconds": timeout_seconds, "costyle_path": str(costyle_path), "command": command},
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HostIntegrationError(
            code="APPLE_EVENT_DENIED",
            message="Capture One CLI command failed. Check command and app permissions.",
            details={"returncode": exc.returncode, "costyle_path": str(costyle_path), "command": command},
        ) from exc


def import_costyle_in_captureone(
    *,
    app_path: str,
    costyle_path: Path,
    timeout_seconds: float,
    launch_mode: Literal["auto", "open", "cli"],
    cli_command: str,
) -> str:
    if launch_mode == "cli":
        _run_cli_import(
            command_template=cli_command,
            app_path=app_path,
            costyle_path=costyle_path,
            timeout_seconds=timeout_seconds,
        )
        return "cli"

    if launch_mode == "open":
        open_costyle_in_captureone(
            app_path=app_path,
            costyle_path=costyle_path,
            timeout_seconds=timeout_seconds,
        )
        return "open"

    cli_error: HostIntegrationError | None = None
    if cli_command.strip():
        try:
            _run_cli_import(
                command_template=cli_command,
                app_path=app_path,
                costyle_path=costyle_path,
                timeout_seconds=timeout_seconds,
            )
            return "cli"
        except HostIntegrationError as exc:
            cli_error = exc

    try:
        open_costyle_in_captureone(
            app_path=app_path,
            costyle_path=costyle_path,
            timeout_seconds=timeout_seconds,
        )
        return "open"
    except HostIntegrationError as exc:
        if cli_error is None:
            raise
        raise HostIntegrationError(
            code=exc.code,
            message=exc.message,
            details={
                "open_error": {"code": exc.code, "message": exc.message, "details": exc.details},
                "cli_error": {
                    "code": cli_error.code,
                    "message": cli_error.message,
                    "details": cli_error.details,
                },
            },
        ) from exc
