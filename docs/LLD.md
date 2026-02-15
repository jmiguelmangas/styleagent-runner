# LLD — StyleAgent Runner (MVP)

## Role
Runner executes backend-defined tasks. It is a thin process and does not embed style business logic.

## Transport
Runner communicates with backend through HTTP.

## Config
Environment variables:
- `RUNNER_API_BASE_URL` (default http://localhost:8000)
- `RUNNER_POLL_INTERVAL` (default 5)
- `RUNNER_API_KEY` (optional placeholder)

## Core modules
- `runner/http.py`: typed requests, retries, timeouts
- `runner/jobs.py`: job dispatcher
- `runner/captureone/compile.py`: calls backend compile endpoint
- `runner/cli.py`: CLI entrypoint and commands
- `runner/types.py`: job models and result models

## Proposed backend API contracts (minimal)
Runner needs endpoints. If backend doesn't have them yet, runner will support a fallback "manual job execution" mode.

Preferred:
- `GET /runner/jobs?status=pending&limit=1`
- `POST /runner/jobs/{job_id}/claim`
- `POST /runner/jobs/{job_id}/heartbeat`
- `POST /runner/jobs/{job_id}/complete`

Fallback (MVP now):
- Runner does not poll; only supports:
  - calling compile endpoint directly for a given style/version
  - used in local dev to test runner plumbing

## Job execution
- Each job produces:
  - `stdout/stderr` log text
  - `result` JSON (artifact_id, sha256, download_url)
  - status = succeeded/failed
