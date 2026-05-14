# AI Handoff Package

## Current Platform State

utility_automation_v2 is a deterministic governance operating platform.

Completed baselines:
- TASK 036: Distributed deterministic mesh
- TASK 037: Policy graph / rollback / persistence
- TASK 038: Advisory governance simulation
- TASK 039: Recovery governance visibility plane
- TASK 041: Incident review console
- TASK 046: DB-backed read-only ops projections
- TASK 047: AI engineering workflow/tooling kit
- TASK 048: Read-only multi-page operator observatory
- TASK 049: Deterministic certification pipeline / governance CI gatekeeper
- TASK 050-A: Security / Dependency Hardening Baseline
- TASK 050-B: Promotion governance workflow / Certification chain established
- TASK 051-A: Promotion Gatekeeper Core implementation

Latest commit: c63baf1a TASK 051-A add promotion gatekeeper core
Current validation: 342 passed
Certification command: PYTHONPATH=. python src/tests/certification/deterministic_certifier.py
Certification artifact: output/certification/certification_artifact.json
CI workflow: .github/workflows/deterministic-certification.yml

Known deferred risk:
- frontend/operator-observatory npm audit reports Next.js/PostCSS vulnerabilities; fix requires breaking Next 16 upgrade

Recommended next task:
- [Next task TBD]

## Non-Negotiable Invariants

1. Ledger is sole source of truth
2. SQLite is projection/cache only
3. Mesh quorum is sole authority
4. AI is advisory only
5. Determinism must not weaken
6. Replay safety required
7. Auditability required
8. Stable canonical ordering required

## Dashboard / UI Scope Rules

Dashboards are observability surfaces.

Allowed:
- GET APIs
- telemetry
- diagnostics
- projections
- visualization
- local presentation state
- filtering of already-fetched projection data when task scope permits

Forbidden:
- governance/runtime mutation
- authority actions
- recovery execution
- policy promotion
- ledger mutation
- quorum bypass

Frontend must:
- preserve backend canonical event ordering unless task explicitly defines alternate derived views
- avoid authority logic
- remain projection-oriented

## Workflow

Before editing:
1. Read PROJECT_RULES.md
2. Read AGENTS.md
3. Inspect task scope
4. Identify authority boundaries

Implementation:
- minimal diffs
- additive changes
- preserve architecture
- targeted validation

Completion:
- run pytest -q
- if runtime/governance changed:
  PYTHONPATH=. python src/tests/certification/deterministic_certifier.py
- report exact outputs

## Additional Completed Baselines
- TASK 051-B: Release Authorization Advisory Bundle
- TASK 051-M: Repository Memory Layer
