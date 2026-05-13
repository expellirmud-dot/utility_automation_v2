# AI Handoff Package for Gemma 4

## Current Status
Latest completed scope:
TASK 039.5 — Recovery Operations Dashboard

Repository contains:
- Distributed deterministic governance mesh
- Policy graph / rollback / persistence
- Advisory governance simulation platform
- Recovery governance platform
- Read-only recovery operations dashboard

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
