# StyleAgent Runner

Thin runner CLI for StyleAgent MVP.

Current status:
- Phase 0: scaffold + CI
- Phase 1: configuration + HTTP client
- Phase 2: minimal job model + execution logs
- Phase 3: polling loop
- Phase 4: on-demand execution by job id

## Setup

```bash
pip install -e .[dev]
```

## CLI

```bash
styleagent-runner --help
```

Run polling loop:

```bash
styleagent-runner poll
```

Run a single poll iteration:

```bash
styleagent-runner poll --once
```

Run one specific job by ID (debug):

```bash
styleagent-runner run --job-id <job_id>
```

## Current MVP Capabilities

- Job type support: `compile_captureone`
- Status transitions: `picked_up -> running -> succeeded/failed`
- Thin execution model: runner calls backend compile endpoint
- Structured execution logs included in job results
- Polling mode and one-shot mode
- On-demand execution mode by backend job id

## Expected Backend Contracts

- `GET /runner/jobs?status=pending&limit=1`
- `GET /runner/jobs/{job_id}`
- `POST /runner/jobs/{job_id}/claim`
- `POST /runner/jobs/{job_id}/heartbeat`
- `POST /runner/jobs/{job_id}/complete`

## Configuration

Environment variables:
- `RUNNER_API_BASE_URL` (default: `http://localhost:8000`)
- `RUNNER_POLL_INTERVAL` (default: `5.0`)
- `RUNNER_API_KEY` (optional, bearer token placeholder)
- `RUNNER_HTTP_TIMEOUT_SECONDS` (default: `10.0`)
- `RUNNER_HTTP_RETRIES` (default: `2`)

## Lint

```bash
ruff check .
```

## Tests

```bash
pytest -q
```

With coverage gate (same as CI):

```bash
pytest --cov=runner --cov-fail-under=85 --cov-report=term-missing -q
```

## Docker

Build image from `runner/`:

```bash
docker build -t styleagent-runner:dev .
```

Run runner in polling mode:

```bash
docker run --rm \
  -e RUNNER_API_BASE_URL=http://host.docker.internal:8000 \
  -e RUNNER_POLL_INTERVAL=5 \
  styleagent-runner:dev
```
