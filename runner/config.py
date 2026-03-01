"""Runner configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import os
from typing import Literal


@dataclass(frozen=True)
class RunnerSettings:
    api_base_url: str = "http://localhost:8000"
    poll_interval_seconds: float = 5.0
    api_key: str | None = None
    http_timeout_seconds: float = 10.0
    http_retries: int = 2
    execution_mode: Literal["api", "host"] = "api"
    captureone_app_path: str = "/Applications/Capture One.app"
    captureone_import_dir: str = "~/.styleagent/captureone/imports"
    captureone_open_timeout_seconds: float = 15.0
    captureone_auto_open: bool = True

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RunnerSettings":
        env = os.environ if environ is None else environ
        api_base_url = env.get("RUNNER_API_BASE_URL", cls.api_base_url).rstrip("/")
        poll_interval_raw = env.get("RUNNER_POLL_INTERVAL")
        api_key = env.get("RUNNER_API_KEY") or None
        timeout_raw = env.get("RUNNER_HTTP_TIMEOUT_SECONDS")
        retries_raw = env.get("RUNNER_HTTP_RETRIES")
        execution_mode = env.get("RUNNER_EXECUTION_MODE", cls.execution_mode).strip().lower()
        captureone_app_path = env.get("RUNNER_CAPTUREONE_APP_PATH", cls.captureone_app_path).strip()
        captureone_import_dir = env.get("RUNNER_CAPTUREONE_IMPORT_DIR", cls.captureone_import_dir).strip()
        open_timeout_raw = env.get("RUNNER_CAPTUREONE_OPEN_TIMEOUT_SECONDS")
        auto_open_raw = env.get("RUNNER_CAPTUREONE_AUTO_OPEN")

        poll_interval_seconds = cls.poll_interval_seconds
        if poll_interval_raw is not None:
            poll_interval_seconds = float(poll_interval_raw)
            if poll_interval_seconds <= 0:
                raise ValueError("RUNNER_POLL_INTERVAL must be > 0")

        http_timeout_seconds = cls.http_timeout_seconds
        if timeout_raw is not None:
            http_timeout_seconds = float(timeout_raw)
            if http_timeout_seconds <= 0:
                raise ValueError("RUNNER_HTTP_TIMEOUT_SECONDS must be > 0")

        http_retries = cls.http_retries
        if retries_raw is not None:
            http_retries = int(retries_raw)
            if http_retries < 0:
                raise ValueError("RUNNER_HTTP_RETRIES must be >= 0")

        if execution_mode not in {"api", "host"}:
            raise ValueError("RUNNER_EXECUTION_MODE must be one of: api, host")

        captureone_open_timeout_seconds = cls.captureone_open_timeout_seconds
        if open_timeout_raw is not None:
            captureone_open_timeout_seconds = float(open_timeout_raw)
            if captureone_open_timeout_seconds <= 0:
                raise ValueError("RUNNER_CAPTUREONE_OPEN_TIMEOUT_SECONDS must be > 0")

        captureone_auto_open = cls.captureone_auto_open
        if auto_open_raw is not None:
            captureone_auto_open = auto_open_raw.strip().lower() in {"1", "true", "yes", "on"}

        return cls(
            api_base_url=api_base_url,
            poll_interval_seconds=poll_interval_seconds,
            api_key=api_key,
            http_timeout_seconds=http_timeout_seconds,
            http_retries=http_retries,
            execution_mode=execution_mode,
            captureone_app_path=captureone_app_path,
            captureone_import_dir=captureone_import_dir,
            captureone_open_timeout_seconds=captureone_open_timeout_seconds,
            captureone_auto_open=captureone_auto_open,
        )
