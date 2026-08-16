# AI Handoff Package for Gemma 4

## Current Status
Latest completed scope:
TASK 046-DB -- Read-only database-backed domain panel projections ✅

Repository contains:
- Distributed deterministic governance mesh
- Policy graph / rollback / persistence
- Advisory governance simulation platform
- Recovery governance platform
- Read-only recovery operations dashboard
- Read-only forensic incident review console
- Read-only DB-backed ops domain panel projections

---

## Latest Completed Scope

TASK 046-DB -- Read-only database-backed domain panel projections ✅

Completed:
- Read-only database projection reader
- DB-backed TASK 046 domain panel formatters
- `/ops/api/recovery`
- `/ops/api/simulation`
- `/ops/api/mesh`
- `/ops/api/policy`
- `/ops/api/replay`
- `/ops/api/system-health`
- `/ops/api/panels`
- Deterministic degraded fallback for missing/unavailable DB
- Projection-only governance tests

Architecture constraints preserved:
- Ledger remains sole source of truth
- SQLite/database remains cache/projection only
- MeshOrchestrator remains sole quorum authority
- AI remains advisory only
- GET-only ops panel APIs
- no POST/PUT/PATCH/DELETE operator routes
- no control-plane imports
- no authority coupling
- no database mutation SQL in the projection reader
- deterministic ordering by explicit stable keys only

Validation:
- pytest -q tests/test_db_projection_reader.py
- pytest -q tests/test_panel_formatters.py
- pytest -q tests/test_ops_domain_panel_governance.py
- pytest -q tests/test_ops_console_shell.py
- pytest -q
- PYTHONPATH=. python src/tests/certification/deterministic_certifier.py

Result:
overall_score: 100.0

---

## Prior Completed Scope

TASK 041 — Operator Incident Review Console ✅

Completed:
- Read-only forensic incident review console
- Provider protocol architecture
- Snapshot-backed live projection adapters
- Incident Explorer
- Decision Lineage Viewer
- Replay Trace Inspector
- Mesh Incident Viewer
- Policy Impact Explorer
- Deterministic analytics summaries
- Expanded provider + API safety tests

Architecture constraints preserved:
- zero write-capable runtime imports
- zero authority coupling
- GET-only API
- deterministic normalization only
- stable sorting keys only
- no timestamp ordering
- snapshot-input only

Validation:
- pip install -r requirements.txt
- pytest tests/test_incident_review.py -q
- pytest tests/test_incident_review_providers.py -q
- pytest tests/validation/test_ledger_integrity.py tests/integration/test_replay_determinism.py -q
- PYTHONPATH=. python src/tests/certification/deterministic_certifier.py

Result:
overall_score: 100.0

---

## Non-Negotiable Architectural Invariants
1. Ledger is sole source of truth
2. SQLite is cache/projection only
3. Mesh authority only
4. AI advisory only
5. No quorum bypass
6. Deterministic guarantees must not weaken

---

## UI / Dashboard Safety Rules
Dashboards and UI APIs are advisory only.

Forbidden:
- POST
- PUT
- PATCH
- DELETE
- forms
- action buttons
- approve/reject/retry/execute/repair flows
- client-side mutation logic

Forbidden imports:
- MeshOrchestrator
- PromotionPipeline
- RecoveryClassifier
- RecoveryPlanBuilder
- RecoverySimulationGate
- RecoveryProposalHandoff
- sqlite3.connect
- write_ledger

---

## Frontend Security Rules
Dynamic API payload rendering:
- use createElement
- use textContent
- use appendChild

Forbidden:
- unsafe innerHTML with API payload content

Allowed:
- static template markup

---

## Determinism Rules
Frontend must:
- preserve backend ordering exactly
- perform no client-side sorting
- perform no client-side filtering
- not rely on object traversal ordering
- not sort by timestamps

Backend must:
- use deterministic ordering by explicit stable keys only

---

## Completed in TASK 039.5
Implemented:
- recovery dashboard API
- recovery dashboard projection DTOs
- recovery dashboard projection service
- deterministic mock fixtures
- read-only HTML/CSS/JS dashboard
- dashboard safety tests

Dashboard source:
RecoveryObservabilityService only

---

## Mission Rule
Proceed only with explicitly assigned task scope.
Do not infer or expand architecture authority.

Follow:
- PROJECT_RULES.md
- AI_HANDOFF.md

Run repository canonical validation/certification commands before completion.
