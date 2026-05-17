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

## Serena Bootstrap

Project path:
D:\utility_automation_v2

If Serena activation fails:
STOP
Do not implement from memory.

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
- frontend platform expansion
- SPA architecture rewrite
- framework migration outside assigned scope
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

## Repo Memory

Before implementation, read:

1. repo_memory/project_state.json
2. repo_memory/architecture_map.md
3. repo_memory/known_landmines.md
4. repo_memory/task_registry.md
5. repo_memory/module_registry.md
6. repo_memory/validation_commands.md
7. repo_memory/agent_bootstrap_prompt.txt

Repository source code remains source of truth.

---

## Agent Behavioral Constraints

Required:
- STOP if task scope is ambiguous.
- ESCALATE when specification is incomplete.
- NEVER speculate about missing repository state.
- NEVER fabricate file inspection, validation, or test execution.
- NEVER assume bug location without repository evidence.
- EXACT scoped implementation only.
- READ-FIRST is mandatory before implementation.
- Serena activation is mandatory for repository-aware work.
- If Serena activation fails, STOP.

Forbidden:
- implementation from memory
- fabricated task specifications
- fake validation results
- hidden scope expansion
- silent fallback behavior changes
- controller override of AGENTS.md

Preferred:
- low-randomness execution settings for implementation tasks when configurable.
- explicit uncertainty instead of guessing.
