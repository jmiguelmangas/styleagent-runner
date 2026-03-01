import httpx
import json

from runner.api import RunnerBackendApi
from runner.config import RunnerSettings
from runner.http import RunnerHttpClient
from runner.types import JobExecutionResult, JobLog


def test_api_lists_jobs_from_items_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/runner/jobs"
        assert request.url.params.get("status") == "pending"
        assert request.url.params.get("limit") == "1"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "job_id": "job_1",
                        "job_type": "compile_captureone",
                        "payload": {"style_id": "style_1", "version": "v1"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000")
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        api = RunnerBackendApi(client)
        jobs = api.list_pending_jobs()

    assert len(jobs) == 1
    assert jobs[0].job_id == "job_1"


def test_api_get_job_by_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/runner/jobs/job_9"
        return httpx.Response(
            200,
            json={
                "job_id": "job_9",
                "job_type": "compile_captureone",
                "payload": {"style_id": "style_9", "version": "v9"},
            },
        )

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000")
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        api = RunnerBackendApi(client)
        job = api.get_job("job_9")

    assert job.job_id == "job_9"
    assert job.payload.style_id == "style_9"
    assert job.payload.version == "v9"


def test_api_complete_job_posts_result_payload() -> None:
    seen_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/complete"):
            seen_payload.update(json.loads(request.read().decode("utf-8")))
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000")
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        api = RunnerBackendApi(client)
        api.complete_job(
            JobExecutionResult(
                job_id="job_1",
                status="succeeded",
                result={"artifact_id": "artifact_1"},
                error=None,
                logs=[
                    JobLog.create(
                        level="info",
                        event="job_succeeded",
                        job_id="job_1",
                        status="succeeded",
                        message="done",
                    )
                ],
            )
        )

    assert seen_payload["status"] == "succeeded"
    assert seen_payload["result"] == {"artifact_id": "artifact_1"}
    assert isinstance(seen_payload["logs"], list)


def test_api_job_calls_include_trace_headers() -> None:
    seen: dict[str, tuple[str | None, str | None]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        request_id = request.headers.get("X-Request-ID")
        runner_job_id = request.headers.get("X-Runner-Job-ID")
        seen[f"{request.method} {request.url.path}"] = (request_id, runner_job_id)

        if request.method == "GET" and request.url.path == "/runner/jobs":
            return httpx.Response(200, json=[])
        if request.method == "POST" and request.url.path == "/runner/jobs/job_42/claim":
            return httpx.Response(200, json={})
        if request.method == "POST" and request.url.path == "/runner/jobs/job_42/heartbeat":
            return httpx.Response(200, json={})
        if request.method == "POST" and request.url.path == "/runner/jobs/job_42/complete":
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    settings = RunnerSettings(api_base_url="http://localhost:8000")
    with RunnerHttpClient(settings, transport=transport, sleep=lambda _: None) as client:
        api = RunnerBackendApi(client)
        _ = api.list_pending_jobs(limit=1)
        api.claim_job("job_42")
        api.heartbeat_job("job_42", status="running")
        api.complete_job(
            JobExecutionResult(
                job_id="job_42",
                status="succeeded",
                result={"artifact_id": "artifact_42"},
                error=None,
                logs=[],
            )
        )

    list_req_id, list_job_header = seen["GET /runner/jobs"]
    assert isinstance(list_req_id, str)
    assert list_req_id.startswith("runner-list-pending-")
    assert list_job_header is None

    claim_req_id, claim_job_header = seen["POST /runner/jobs/job_42/claim"]
    assert isinstance(claim_req_id, str)
    assert claim_req_id.startswith("runner-claim-job_42-")
    assert claim_job_header == "job_42"

    hb_req_id, hb_job_header = seen["POST /runner/jobs/job_42/heartbeat"]
    assert isinstance(hb_req_id, str)
    assert hb_req_id.startswith("runner-heartbeat-job_42-")
    assert hb_job_header == "job_42"

    complete_req_id, complete_job_header = seen["POST /runner/jobs/job_42/complete"]
    assert isinstance(complete_req_id, str)
    assert complete_req_id.startswith("runner-complete-job_42-")
    assert complete_job_header == "job_42"
