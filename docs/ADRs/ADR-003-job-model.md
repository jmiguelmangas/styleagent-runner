# ADR-003: Minimal job model

Status: Accepted

## Decision
MVP supports only one job type:
- compile_captureone

One job at a time. No concurrency in MVP.

## Rationale
Keeps runner simple and testable.
