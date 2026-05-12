# Utility Automation V2 — AI Work Rules

## Current Platform State

This repository is a deterministic governance operating platform.

Completed baselines:
- TASK 036: Certified deterministic distributed mesh
- TASK 037: Policy graph, rollback, persistence, time-travel audit
- TASK 038-S1: Advisory governance simulation
- TASK 038-S2: Simulation scenario engine

## Non-Negotiable Architecture Rules

1. Ledger is the only source of truth.
2. SQLite is cache/projection only.
3. MeshOrchestrator is the only quorum authority.
4. AI is advisory only.
5. Simulation must never write ledger events.
6. Simulation must never call promotion or quorum APIs.
7. Never weaken hash, signature, invariant, replay, quorum, or audit determinism.
8. All reports must be deterministic and hashable.
9. All ordering must be canonical and stable.
10. If a test fails, fix root cause, never weaken tests.

## Required Workflow

Before editing:
1. Inspect relevant modules.
2. Identify authority boundaries.
3. State intended files to change.
4. Do not redesign architecture unless explicitly instructed.

During implementation:
1. Prefer additive modules.
2. Keep side effects isolated.
3. Use frozen dataclasses for reports/models.
4. Keep AI output outside deterministic hashes.
5. Preserve source-of-truth boundaries.

After implementation:
1. Run targeted tests.
2. Run deterministic certification.
3. Report files changed.
4. Report test output.
5. Report remaining risks.

## Model Usage Guidance

- GPT-5.5: architecture audit, correctness review, final gate
- Claude Sonnet: multi-file implementation
- Gemma 4: long-context architecture stitching and roadmap
- Gemini Flash 3.1: boilerplate, API wrappers, test scaffolding, dashboard plumbing

## Current Recommended Next Task

TASK 038-S3 — Simulation Report API / Operator Review Surface

Scope:
- expose simulation/scenario reports through API/service layer
- no dashboard yet
- no ledger writes
- no promotion calls
- reports are cache artifacts only
