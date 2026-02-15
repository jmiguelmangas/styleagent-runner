"""HTTP wrapper for backend communication with retries and timeout support."""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

import httpx

from runner.config import RunnerSettings


class RunnerHttpError(RuntimeError):
    """Raised when backend communication fails."""


class RunnerHttpClient:
    def __init__(
        self,
        settings: RunnerSettings,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        headers = {"User-Agent": "styleagent-runner/0.1.0"}
        if settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"

        self._retries = settings.http_retries
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=settings.api_base_url,
            timeout=settings.http_timeout_seconds,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RunnerHttpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        last_error: Exception | None = None

        for attempt in range(self._retries + 1):
            try:
                response = self._client.request(method, path, json=json, params=params)
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == self._retries:
                    break
                self._sleep(_backoff_seconds(attempt))
                continue

            if response.status_code >= 500:
                last_error = RunnerHttpError(
                    f"Backend server error: {response.status_code} for {method.upper()} {path}"
                )
                if attempt == self._retries:
                    break
                self._sleep(_backoff_seconds(attempt))
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RunnerHttpError(str(exc)) from exc

            if not response.content:
                return {}

            return response.json()

        raise RunnerHttpError("Backend request failed after retries") from last_error


def _backoff_seconds(attempt: int) -> float:
    return 0.25 * (2**attempt)

