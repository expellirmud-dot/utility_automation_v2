# Strict Task Prompt

Read first:
- PROJECT_RULES.md
- AI_HANDOFF.md
- AGENTS.md

Work only within the explicitly assigned task scope.

Rules:
- no architecture expansion
- no framework migration
- no speculative refactor
- no unrelated cleanup
- no authority escalation
- preserve deterministic guarantees
- preserve repository invariants

Implementation style:
- minimal diffs
- localized edits
- additive changes when possible
- deterministic ordering
- stable outputs

Before completion:
- run targeted tests
- run python -m pytest -q
- if governance/runtime behavior changed, run deterministic certifier

Report:
- files changed
- tests run
- exact results
- remaining risks
