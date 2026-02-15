import httpx

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

