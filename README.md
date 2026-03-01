# StyleAgent Runner

Thin runner CLI for StyleAgent MVP.

Current status:
- Phase 0: scaffold + CI
- Phase 1: configuration + HTTP client
- Phase 2: minimal job model + execution logs
- Phase 3: polling loop
- Phase 4: on-demand execution by job id
- Host mode: optional Capture One desktop app open/import after compile

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

Run host preflight diagnostics:

```bash
styleagent-runner doctor
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
- `RUNNER_EXECUTION_MODE` (`api` or `host`, default: `api`)
- `RUNNER_CAPTUREONE_AUTO_OPEN` (`true`/`false`, default: `true`)
- `RUNNER_CAPTUREONE_APP_PATH` (default: `/Applications/Capture One.app`)
- `RUNNER_CAPTUREONE_IMPORT_DIR` (default: `~/.styleagent/captureone/imports`)
- `RUNNER_CAPTUREONE_OPEN_TIMEOUT_SECONDS` (default: `15`)
- `RUNNER_CAPTUREONE_LAUNCH_MODE` (`auto`, `open`, or `cli`, default: `auto`)
- `RUNNER_CAPTUREONE_CLI_COMMAND` (optional template, supports `{app_path}` and `{costyle_path}`)

Host-mode example (macOS):

```bash
RUNNER_EXECUTION_MODE=host \
RUNNER_CAPTUREONE_APP_PATH="/Applications/Capture One.app" \
styleagent-runner poll --once
```

Host-mode with CLI command (strict CLI mode):

```bash
RUNNER_EXECUTION_MODE=host \
RUNNER_CAPTUREONE_LAUNCH_MODE=cli \
RUNNER_CAPTUREONE_CLI_COMMAND='captureone-cli import --style {costyle_path}' \
styleagent-runner poll --once
```

In `auto` mode, runner tries `RUNNER_CAPTUREONE_CLI_COMMAND` first (if configured) and
falls back to `open -a` on failure.

Doctor command returns:
- exit `0` when Capture One host prerequisites are ready
- exit `1` when one or more checks fail
- JSON diagnostic report to stdout

Host execution failure taxonomy (job result `host_integration.error_code`):
- `APP_NOT_INSTALLED`
- `APPLE_EVENT_DENIED`
- `OPEN_TIMEOUT`
- `IMPORT_DIR_NOT_WRITABLE`
- `DOWNLOAD_FAILED`

## Observability

- Runner adds `X-Request-ID` to backend calls for traceability.
- For job-specific calls (`claim`, `heartbeat`, `complete`), request ids include the job id:
  - `runner-<action>-<job_id>-<suffix>`
- Runner also sends `X-Runner-Job-ID` for job-specific backend requests.
- Backend echoes `X-Request-ID`, so you can correlate runner logs and backend access logs.

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

Local host integration test (opt-in, macOS):

```bash
RUNNER_HOST_IT=1 \
RUNNER_API_BASE_URL=http://localhost:8000 \
RUNNER_EXECUTION_MODE=host \
RUNNER_CAPTUREONE_APP_PATH="/Applications/Capture One.app" \
pytest -q tests/integration/test_host_local_integration.py
```

Prerequisites:
- backend is running and reachable at `RUNNER_API_BASE_URL`
- Capture One app is installed locally

## Automation

- `.github/dependabot.yml` creates weekly dependency update PRs
- `.github/workflows/sbom.yml` generates a CycloneDX SBOM artifact
- `.github/workflows/host-integration.yml` runs real host integration checks on self-hosted macOS runners
  with label `captureone` (scheduled weekly and runnable manually)

### Host Workflow Readiness Checklist

The `Host Integration (macOS)` workflow requires a self-hosted GitHub Actions runner with labels:
- `self-hosted`
- `macOS`
- `captureone`

Repository-level setup required in `styleagent-runner`:
- Add at least one self-hosted runner with the labels above.
- Ensure Capture One is installed on that machine.
- Optional variables (`Settings > Secrets and variables > Actions > Variables`):
  - `RUNNER_CAPTUREONE_APP_PATH`
  - `RUNNER_CAPTUREONE_IMPORT_DIR`
  - `RUNNER_CAPTUREONE_LAUNCH_MODE`
  - `RUNNER_CAPTUREONE_CLI_COMMAND`

Verification:
- Trigger workflow manually:

```bash
gh workflow run "Host Integration (macOS)" -R jmiguelmangas/styleagent-runner --ref main
```

- Confirm it starts immediately (not stuck in `queued`) and completes `success`.

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
