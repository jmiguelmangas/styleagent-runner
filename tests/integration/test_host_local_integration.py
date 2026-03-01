import os
import platform
import uuid
from pathlib import Path

import httpx
import pytest

from runner.captureone.compile import run_compile_captureone
from runner.config import RunnerSettings
from runner.http import RunnerHttpClient
from runner.types import CompileCaptureOnePayload


def _require_host_it() -> RunnerSettings:
    if os.getenv("RUNNER_HOST_IT") != "1":
        pytest.skip("Set RUNNER_HOST_IT=1 to run local host integration tests")
    if platform.system() != "Darwin":
        pytest.skip("Host integration tests currently target macOS only")

    settings = RunnerSettings.from_env(os.environ)
    app_path = Path(settings.captureone_app_path).expanduser()
    if not app_path.exists():
        pytest.skip(f"Capture One app not found at {app_path}")

    return settings


def _backend_ready(settings: RunnerSettings) -> bool:
    try:
        response = httpx.get(f"{settings.api_base_url}/health", timeout=3.0)
        return response.status_code == 200
    except Exception:
        return False


def _create_style_and_version(settings: RunnerSettings) -> tuple[str, str]:
    style_name = f"runner-host-it-{uuid.uuid4().hex[:8]}"
    with httpx.Client(base_url=settings.api_base_url, timeout=10.0) as client:
        style_response = client.post("/styles", json={"name": style_name})
        style_response.raise_for_status()
        style_id = style_response.json()["style_id"]

        version = "it-host-v1"
        spec = {
            "version": version,
            "style_spec": {
                "name": style_name,
                "intent": ["integration", "host"],
                "captureone": {"keys": {"Exposure": 0.2, "Contrast": 6}},
            },
        }
        version_response = client.post(f"/styles/{style_id}/versions", json=spec)
        version_response.raise_for_status()

    return style_id, version


@pytest.mark.integration
@pytest.mark.host_local
def test_host_local_compile_import_roundtrip() -> None:
    settings = _require_host_it()
    if not _backend_ready(settings):
        pytest.skip(
            f"Backend is not reachable at {settings.api_base_url}. Start platform stack first."
        )

    style_id, version = _create_style_and_version(settings)

    host_settings = RunnerSettings(
        **{
            **settings.__dict__,
            "execution_mode": "host",
            "captureone_auto_open": True,
        }
    )

    payload = CompileCaptureOnePayload(style_id=style_id, version=version, execution_mode="host")
    with RunnerHttpClient(host_settings) as client:
        result = run_compile_captureone(client, payload, settings=host_settings)

    host = result.get("host_integration")
    assert isinstance(host, dict)
    assert host.get("mode") == "host"
    assert host.get("launch_method") in {"open", "cli"}

    imported = host.get("imported_costyle_path")
    assert isinstance(imported, str) and imported
    assert Path(imported).exists()
