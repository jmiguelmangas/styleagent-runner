# ADR-001: Runner is a thin worker (MVP)

Status: Accepted

## Decision
Runner will NOT replicate style compilation logic.
Runner only orchestrates execution by calling backend endpoints.

## Rationale
Single source of truth in backend; avoids divergence and duplicated logic.
