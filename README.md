# StyleAgent Runner

Thin runner CLI for StyleAgent MVP.

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
