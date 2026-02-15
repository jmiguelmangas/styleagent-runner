# StyleAgent Runner — AGENTS.md

## Goal
Provide a lightweight Runner service/CLI that can execute backend-defined jobs locally for MVP.
MVP target: Capture One only.

## Scope (MVP)
- Poll backend for pending jobs OR run a single job on demand.
- Execute Capture One compile tasks by calling backend compile endpoint (thin runner).
- Store logs and report job result back to backend.

## Non-goals (MVP)
- No DaVinci/LR
- No SDK/CLI integrations
- No queue infra (Redis/SQS)
- No GPU/accelerated processing

## Working rules
- Small PRs, always via branches.
- Add tests for job orchestration and CLI.
- No direct changes to backend contracts: treat API as external.

## Commands
- Install: `pip install -e .[dev]`
- Run CLI: `styleagent-runner --help`
- Tests: `pytest -q`
- Lint: `ruff check .`
