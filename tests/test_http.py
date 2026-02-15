import httpx
import pytest

from runner.config import RunnerSettings
from runner.http import RunnerHttpClient, RunnerHttpError


def test_http_client_retries_on_5xx_then_succeeds() -> None:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(500, json={"message": "temporary"})
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000", http_retries=2)
    client = RunnerHttpClient(settings, transport=transport, sleep=lambda _: None)
    result = client.request_json("GET", "/health")
    client.close()

    assert result == {"ok": True}
    assert calls["count"] == 2


def test_http_client_retries_on_network_error_then_succeeds() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000", http_retries=1)
    client = RunnerHttpClient(settings, transport=transport, sleep=lambda _: None)
    result = client.request_json("GET", "/health")
    client.close()

    assert result == {"status": "ok"}
    assert calls["count"] == 2


def test_http_client_4xx_raises_without_retry() -> None:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000", http_retries=5)
    client = RunnerHttpClient(settings, transport=transport, sleep=lambda _: None)

    with pytest.raises(RunnerHttpError):
        client.request_json("GET", "/missing")
    client.close()

    assert calls["count"] == 1


def test_http_client_sends_api_key_header() -> None:
    seen_auth_header = {"value": None}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth_header["value"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        api_key="runner-token",
        http_retries=0,
    )
    client = RunnerHttpClient(settings, transport=transport, sleep=lambda _: None)
    _ = client.request_json("GET", "/health")
    client.close()

    assert seen_auth_header["value"] == "Bearer runner-token"

