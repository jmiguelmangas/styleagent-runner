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
    assert host_info["launch_method"] == "open"
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
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["error_code"] == "APP_NOT_INSTALLED"
    assert result.error is not None
    assert "APP_NOT_INSTALLED" in result.error


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
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["launch_method"] == "open"


def test_job_executor_host_mode_reports_download_failed(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_200",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_200",
                },
            )
        return httpx.Response(500, json={"detail": "boom"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(tmp_path / "imports"),
    )
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_6",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "failed"
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["error_code"] == "DOWNLOAD_FAILED"


def test_job_executor_host_mode_reports_open_timeout(tmp_path, monkeypatch) -> None:
    def fake_run(cmd: list[str], check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr("runner.captureone.host.subprocess.run", fake_run)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_300",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_300",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_300":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(tmp_path / "imports"),
    )
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_7",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "failed"
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["error_code"] == "OPEN_TIMEOUT"


def test_job_executor_host_mode_cli_launch_success(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {"cmd": None}

    def fake_run(cmd: list[str], check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        assert check is True
        assert timeout == 15.0
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("runner.captureone.host.subprocess.run", fake_run)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_901",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_901",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_901":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    import_dir = tmp_path / "imports"

    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(import_dir),
        captureone_launch_mode="cli",
        captureone_cli_command="captureone-cli import --style {costyle_path}",
    )
    with RunnerHttpClient(settings, transport=httpx.MockTransport(handler), sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_cli_1",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "succeeded"
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["launch_method"] == "cli"
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[:3] == ["captureone-cli", "import", "--style"]
    assert cmd[-1] == str(import_dir / "artifact_901.costyle")


def test_job_executor_host_mode_cli_requires_command(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_902",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_902",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_902":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(tmp_path / "imports"),
        captureone_launch_mode="cli",
        captureone_cli_command="",
    )
    with RunnerHttpClient(settings, transport=httpx.MockTransport(handler), sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_cli_2",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "failed"
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["error_code"] == "APP_NOT_INSTALLED"


def test_job_executor_host_mode_auto_falls_back_to_open_when_cli_fails(tmp_path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool, timeout: float) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        assert check is True
        assert timeout == 15.0
        if cmd and cmd[0] == "captureone-cli":
            raise subprocess.CalledProcessError(returncode=2, cmd=cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("runner.captureone.host.subprocess.run", fake_run)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/styles/style_1/versions/v1/compile":
            return httpx.Response(
                200,
                json={
                    "artifact_id": "artifact_903",
                    "sha256": "abc123",
                    "download_url": "/artifacts/artifact_903",
                },
            )
        if request.method == "GET" and request.url.path == "/artifacts/artifact_903":
            return httpx.Response(200, content=b"<SL Engine='13'>")
        return httpx.Response(404, json={"detail": "not found"})

    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    import_dir = tmp_path / "imports"
    settings = RunnerSettings(
        api_base_url="http://localhost:8000",
        http_retries=0,
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(import_dir),
        captureone_launch_mode="auto",
        captureone_cli_command="captureone-cli import --style {costyle_path}",
    )
    with RunnerHttpClient(settings, transport=httpx.MockTransport(handler), sleep=lambda _: None) as client:
        executor = JobExecutor(client, settings=settings)
        job = Job(
            job_id="job_cli_3",
            job_type="compile_captureone",
            payload=CompileCaptureOnePayload(style_id="style_1", version="v1"),
        )
        result = executor.execute(job)

    assert result.status == "succeeded"
    assert result.result is not None
    host_info = result.result.get("host_integration")
    assert isinstance(host_info, dict)
    assert host_info["launch_method"] == "open"
    assert len(calls) == 2
    assert calls[0][0] == "captureone-cli"
    assert calls[1][:2] == ["open", "-a"]
