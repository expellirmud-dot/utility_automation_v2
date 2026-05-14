# AGENTS.md

## Repository Identity

This repository is a deterministic governance platform.

Core invariants:
- Ledger is the sole source of truth.
- SQLite is projection/cache only.
- Mesh quorum is the only authority for committed state transitions.
- AI is advisory only.
- Determinism is mandatory.
- Certification integrity must be preserved.

---

## Mandatory Read Order

Before making changes:

1. PROJECT_RULES.md
2. AI_HANDOFF.md
3. Current assigned task scope

Do not proceed without understanding repository constraints.

---

## Scope Discipline

Allowed:
- implement explicitly assigned task scope
- minimal targeted fixes
- additive functionality
- localized refactors required by the task

Forbidden:
- speculative refactors
- repo-wide cleanup
- unrelated rewrites
- framework migrations
- architecture expansion
- silent dependency changes
- hidden infrastructure changes

---

## Forbidden Authority Changes

Never introduce or modify without explicit instruction:

- ledger mutation semantics
- quorum authority rules
- policy promotion authority
- replay authority
- recovery execution authority
- trust model changes
- authentication redesign
- mesh consensus redesign

---

## Dashboard Constraints

Ops surfaces are read-only.

Allowed:
- GET endpoints
- telemetry
- diagnostics
- projections
- visual UI improvements

Forbidden:
- POST
- PUT
- PATCH
- DELETE
- mutation APIs
- action buttons
- replay triggers
- recovery execution
- policy promotion
- control-plane mutation flows

---

## Frontend Constraints

If improving dashboard UI:

Allowed:
- static HTML/CSS/JS improvements
- layout modernization
- typography
- cards
- badges
- charts
- loading/empty/degraded states

Forbidden unless explicitly assigned:
- Next.js migration
- React migration
- SPA architecture rewrite
- server actions
- frontend authority logic

---

## Coding Discipline

Prefer:
- deterministic implementations
- explicit ordering
- stable outputs
- minimal diffs
- existing architecture reuse

Avoid:
- global mutable state
- time-dependent ambiguity
- hidden randomness
- silent fallback behavior changes

---

## Validation Requirements

Before declaring completion:

Required:
python -m pytest -q

If governance/runtime affected:
python src/tests/certification/deterministic_certifier.py

Report exact results.

Never claim completion without validation.