"""Capture One compile job implementation."""

from __future__ import annotations

from typing import Any

from runner.http import RunnerHttpClient
from runner.types import CompileCaptureOnePayload


def run_compile_captureone(
    client: RunnerHttpClient,
    payload: CompileCaptureOnePayload,
) -> dict[str, Any]:
    return client.request_json(
        "POST",
        f"/styles/{payload.style_id}/versions/{payload.version}/compile",
        params={"target": "captureone"},
    )

