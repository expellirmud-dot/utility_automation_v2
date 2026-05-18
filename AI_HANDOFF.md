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
- TASK 052 housekeeping update handoff
TASK 053 housekeeping update handoff
TASK 054 housekeeping update handoff
TASK 055 housekeeping update handoff
TASK 056 housekeeping update handoff
TASK 057 housekeeping update handoff
- added deterministic evidence package provider
- added GET-only /api/ops/evidence-package
- added operator observatory evidence package review surface
- frontend proxy/schema/types/client/sidebar integration
- validation passed:
  pytest
  deterministic certifier
  next build
  typecheck

TASK 058 update handoff and project state
TASK 059 update handoff and project state
TASK 060 update handoff and project state
TASK 061 update handoff and project state
TASK 062 update handoff and project state
TASK 063 update handoff and project state
TASK 064 repository workflow memory hardening
- TASK 065 Governance Review Index Bundle
  - Deterministic audit index consolidating governance hashes
  -- Backend-only implementation (no API/UI/IO)
  -- Validates hash integrity and structural readiness
  -- Deterministic blocked statuses for missing references
  - Validation passed: pytest, deterministic certifier
- TASK 066 Governance Review Index Surface
  - Read-only operator review surface for the Review Index Bundle
  -- GET-only backend API and observational frontend page
  -- No mutation or authority logic
  -- Deterministic degraded state for missing references
  - Validation passed: pytest, deterministic certifier, frontend build/typecheck
- TASK 067 Governance Review Index Source Reference Hardening
  - Hardened source reference extraction for the Review Index
  -- deterministic extraction of existing hashes from source projections
  -- no fabricated provenance
  -- preserved blocked status for missing references
  - Validation passed: pytest, deterministic certifier
- TASK 068 Evidence Projection Reconstruction Hardening
  - Fixed reconstruction of frozen domain models from projection dictionaries
  -- strips derived fields (package_hash, report_hash) before constructor call
  -- prevents TypeError in readiness and summary providers
  - Validation passed: pytest, deterministic certifier
- TASK 071 Governance Execution Contract Layer
  - Deterministic contract models and validator for worker execution
- TASK 072 Runtime Contract Guard Foundation
  - Programmatic guard service to validate execution contracts before implementation
- TASK 073 Execution Contract Validator
- TASK 074 AI Runtime Contract CLI Foundation
- TASK 075 Completion Evidence Provenance Generator
- TASK 076 Runtime Evidence Standardization
- TASK 077 Runtime Execution Enforcement Gate
- TASK 078 Controller Request Governance
- TASK 079 Controller Request Template Generator
- TASK 080 Runtime Contract Lifecycle Inspector
- TASK 081 Controller Runtime Automation Harness
- TASK 082 Documentation Governance Consolidation
- TASK 083 AI Context Canonical Source Audit
- TASK 084 Runtime Post-Task Automation Harness
- TASK 085 Unified Runtime Control Console
- TASK 086 Interactive Runtime Operator Console UX
- TASK 087 Runtime Web Operator Console Foundation
- TASK 088 Runtime Operator Control Actions
- TASK 089 Runtime Operator Control Forms UX
- TASK 090 Runtime Progress and Evidence Viewer
- TASK 091: Runtime Task Templates / Quick Launch UX
- TASK 092: Runtime timeline and task history UX
- TASK 093: Runtime Artifact Browser UX
  - Artifact Browser implemented in Operator Observatory
  - Backend: `GET /api/ops/runtime-tasks/{task_id}?include_contents=true`
  - Frontend: `ArtifactBrowser` component in `page.tsx`
  - Validation passed:
    - pytest
    - deterministic certifier 100.0
    - next build
    - typecheck

no Dynamic server usage warning
npm build passed
npm typecheck passed

Certification command: PYTHONPATH=. python src/tests/certification/deterministic_certifier.py
Certification artifact: output/certification/certification_artifact.json
CI workflow: .github/workflows/deterministic-certification.yml

Known deferred risk:
- frontend/operator-observatory npm audit reports Next.js/PostCSS vulnerabilities; fix requires breaking Next 16
 upgrade

Recommended next task:
- TASK 094 [TBD]


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
- TASK 051-C: Release Governance Review Surface
  - route /release-governance
  - proxy /api/ops/release-governance
  - backend GET /ops/api/release-governance
  - validation status: passed
