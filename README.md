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
- TASK 048 Read-only multi-page operator observatory
- TASK 049 Deterministic certification pipeline
- TASK 050-A Security/Dependency Hardening Baseline
- TASK 050-B Promotion governance workflow
- TASK 051-A Promotion Gatekeeper Core
- TASK 051-B Release Authorization Advisory Bundle
- TASK 051-M Repository local AI memory layer
- TASK 071-081 Runtime Contract Guard and Lifecycle Harness
- TASK 082 Documentation Governance Consolidation
- TASK 083 AI Context Canonical Source Audit
- TASK 084 Runtime Post-Task Harness
- TASK 085-091 Unified Runtime Control Console & Web Operator Console UX
- TASK 092-094 Timeline, Task History, and Artifact Browser/Export UX
- TASK 095-097 Governance Workbench & Runtime baseline reset
- TASK 098 Runtime Governance History Reconciliation (Transitional)
- TASK 099 Runtime Governance Transition (Transitional)
- TASK 100 Runtime Governance Continuity Baseline

## Validation

Canonical validation:

python -m pytest -q
PYTHONPATH=. python src/tests/certification/deterministic_certifier.py

