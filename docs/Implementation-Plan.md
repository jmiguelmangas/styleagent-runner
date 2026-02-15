# StyleAgent Runner — Implementation Plan (MVP)

Runner MVP is intentionally small. It will act as a thin worker that:
- asks backend for work
- executes work by calling backend endpoints
- reports status back

## Phase 0 — Scaffold + CI
- Create python package (pyproject.toml)
- Add ruff + pytest
- Add GitHub Actions CI (lint + tests)
- Add minimal CLI entrypoint

## Phase 1 — Configuration + HTTP client
- `RUNNER_API_BASE_URL` env var
- API key optional placeholder
- HTTP wrapper with retries + timeouts

## Phase 2 — Job model (minimal)
- Define Job types:
  - `compile_captureone`
- Define job state transitions:
  - `picked_up` -> `running` -> `succeeded/failed`
- Implement job execution locally with structured logs

## Phase 3 — Polling loop
- Command: `styleagent-runner poll`
- Poll backend every N seconds
- Pick one job at a time (MVP)
- Report results back

## Phase 4 — On-demand execution
- Command: `styleagent-runner run --job-id <id>`
- Useful for debugging

MVP complete after Phase 3.
