import httpx
import subprocess

from runner.config import RunnerSettings
from runner.http import RunnerHttpClient
from runner.jobs import JobExecutor
from runner.types import CompileCaptureOnePayload, Job


def test_job_executor_compile_captureone_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/styles/style_1/versions/v1/compile"
        assert request.url.params.get("target") == "captureone"
        return httpx.Response(
            200,
            json={
                "artifact_id": "artifact_123",
                "sha256": "abc123",
                "download_url": "http://localhost:8000/artifacts/artifact_123",
            },
        )

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000", http_retries=0)
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client)
        job = Job(
            job_id="job_1",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )

        result = executor.execute(job)

    assert result.status == "succeeded"
    assert result.error is None
    assert result.result is not None
    assert result.result["artifact_id"] == "artifact_123"
    assert [log.event for log in result.logs] == ["job_picked_up", "job_running", "job_succeeded"]
    assert all({"timestamp", "level", "event", "job_id", "status", "message", "context"} <= set(log.to_dict().keys()) for log in result.logs)


def test_job_executor_compile_captureone_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "backend down"})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000", http_retries=0)
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client)
        job = Job(
            job_id="job_2",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v2"),
        )

        result = executor.execute(job)

    assert result.status == "failed"
    assert result.result is None
    assert result.error is not None
    assert [log.event for log in result.logs] == ["job_picked_up", "job_running", "job_failed"]
    assert result.logs[-1].level == "error"


def test_job_executor_host_mode_opens_artifact_in_captureone(tmp_path, monkeypatch) -> None:
    opened = {"cmd": None}

    def fake_run(cmd: list[str], check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        opened["cmd"] = cmd
        assert check is True
        assert timeout == 15.0
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("runner.captureone.host.subprocess.run", fake_run)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_123",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_123",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_123":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    import_dir = tmp_path / "imports"

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(import_dir),
    )
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_3",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "succeeded"
    assert result.error is None
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["mode"] == "host"
    imported_path = import_dir / "artifact_123.costyle"
    assert imported_path.exists()
    assert imported_path.read_bytes() == b"<SL Engine='13'>"
    assert opened["cmd"] is not None
    assert opened["cmd"][-1] == str(imported_path)


def test_job_executor_host_mode_fails_when_captureone_missing(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_123",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_123",
                },
            )
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(tmp_path / "Missing Capture One.app"),
        captureone_import_dir=str(tmp_path / "imports"),
    )
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_4",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "failed"
    assert result.result is None
    assert result.error is not None
    assert "Capture One app not found" in result.error


def test_job_executor_payload_host_mode_overrides_api_settings(tmp_path, monkeypatch) -> None:
    opened = {"count": 0}

    def fake_run(cmd: list[str], check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        opened["count"] += 1
        assert check is True
        assert timeout == 15.0
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("runner.captureone.host.subprocess.run", fake_run)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_777",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_777",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_777":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    import_dir = tmp_path / "imports"

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="api",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(import_dir),
    )
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_5",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1", execution_mode="host"),
        )
        result = executor.execute(job)

    assert result.status == "succeeded"
    assert opened["count"] == 1
    assert (import_dir / "artifact_777.costyle").exists()
