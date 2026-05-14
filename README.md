# Utility Automation V2

Deterministic governance operating platform.

## Core Truth Model

- Ledger is sole source of truth
- SQLite is projection/cache only
- Mesh quorum is sole authority
- AI is advisory only

## Platform Properties

- deterministic replay
- auditability
- governance integrity
- stable canonical ordering
- certification reproducibility

## Completed Baselines

- TASK 036 Distributed deterministic mesh
- TASK 037 Policy governance graph
- TASK 038 Advisory simulation platform
- TASK 039 Recovery governance visibility
- TASK 041 Incident review console
- TASK 046 DB-backed read-only ops projections
- TASK 047 AI engineering workflow kit

## Validation

Canonical validation:

python -m pytest -q
PYTHONPATH=. python src/tests/certification/deterministic_certifier.py
