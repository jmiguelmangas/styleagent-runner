"""Runner configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import os


@dataclass(frozen=True)
class RunnerSettings:
    api_base_url: str = "http://localhost:8000"
    api_key: str | None = None
    http_timeout_seconds: float = 10.0
    http_retries: int = 2

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RunnerSettings":
        env = os.environ if environ is None else environ
        api_base_url = env.get("RUNNER_API_BASE_URL", cls.api_base_url).rstrip("/")
        api_key = env.get("RUNNER_API_KEY") or None
        timeout_raw = env.get("RUNNER_HTTP_TIMEOUT_SECONDS")
        retries_raw = env.get("RUNNER_HTTP_RETRIES")

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

        return cls(
            api_base_url=api_base_url,
            api_key=api_key,
            http_timeout_seconds=http_timeout_seconds,
            http_retries=http_retries,
        )

