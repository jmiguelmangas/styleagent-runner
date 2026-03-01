"""Capture One compile job implementation."""

from __future__ import annotations

from typing import Any

from runner.captureone.host import (
    HostIntegrationError,
    build_import_output_path,
    ensure_captureone_app_exists,
    import_costyle_in_captureone,
)
from runner.config import RunnerSettings
from runner.http import RunnerHttpClient
from runner.types import CompileCaptureOnePayload


def run_compile_captureone(
    client: RunnerHttpClient,
    payload: CompileCaptureOnePayload,
    settings: RunnerSettings | None = None,
) -> dict[str, Any]:
    compile_result = client.request_json(
        "POST",
        f"/styles/{payload.style_id}/versions/{payload.version}/compile",
        params={"target": "captureone"},
    )
    if not isinstance(compile_result, dict):
        raise ValueError("Invalid compile response payload")

    effective_mode = payload.execution_mode
    if settings is not None and effective_mode == "api":
        effective_mode = settings.execution_mode

    if settings is None or effective_mode != "host" or not settings.captureone_auto_open:
        return compile_result

    host_context: dict[str, Any] = {
        "mode": "host",
        "captureone_app_path": settings.captureone_app_path,
        "import_dir": settings.captureone_import_dir,
    }

    artifact_id = compile_result.get("artifact_id")
    download_url = compile_result.get("download_url")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("Compile response missing artifact_id")
    if not isinstance(download_url, str) or not download_url:
        raise ValueError("Compile response missing download_url")

    try:
        app_path = str(ensure_captureone_app_exists(settings.captureone_app_path))
        host_context["captureone_app_path"] = app_path
        artifact_bytes = client.request_bytes("GET", download_url)
    except HostIntegrationError:
        raise
    except Exception as exc:
        raise HostIntegrationError(
            code="DOWNLOAD_FAILED",
            message="Failed to download compiled artifact from backend",
            details={**host_context, "download_url": download_url, "error": str(exc)},
        ) from exc

    try:
        output_path = build_import_output_path(settings.captureone_import_dir, artifact_id)
        output_path.write_bytes(artifact_bytes)
    except HostIntegrationError:
        raise
    except Exception as exc:
        raise HostIntegrationError(
            code="IMPORT_DIR_NOT_WRITABLE",
            message="Failed to write .costyle artifact to import directory",
            details={**host_context, "artifact_id": artifact_id, "error": str(exc)},
        ) from exc

    launch_method = import_costyle_in_captureone(
        app_path=app_path,
        costyle_path=output_path,
        timeout_seconds=settings.captureone_open_timeout_seconds,
        launch_mode=settings.captureone_launch_mode,
        cli_command=settings.captureone_cli_command,
    )

    return {
        **compile_result,
        "host_integration": {
            "mode": "host",
            "launch_method": launch_method,
            "captureone_app_path": app_path,
            "imported_costyle_path": str(output_path),
        },
    }
