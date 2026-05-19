# Controller Execution Request

## Task ID
TASK-097

## Title
Hardening runtime governance and establishing task baseline

## Authority
Human-approved controller request

## Objective
Introduce certifier check to enforce runtime task contract and report completeness for post-baseline tasks, while exempting legacy tasks <= 96

## Architectural rationale
Provides fail-closed assurance that future changes comply with the execution contract framework without allowing bypasses

## Scope

### In scope
- src/tests/certification/certification_checks.py
- src/tests/certification/runtime_task_governance_checks.py
- repo_memory/task_registry.md
- AI_HANDOFF.md

### Candidate modules
src/tests/certification/certification_checks.py
src/tests/certification/runtime_task_governance_checks.py

### Runtime artifacts
ai_runtime/contracts/
ai_runtime/completions/
ai_runtime/reports/
ai_runtime/inbox/

### Tests
tests/test_certification_pipeline.py

## Constraints
- ledger remains sole source of truth
- SQLite is projection/cache only
- AI advisory only
- no autonomous authority mutation
- no self-approval
- no hidden execution channels
- no frontend authority expansion
- preserve existing workflow

## Non-goals
- autonomous task planning
- automatic scope invention
- scheduler design
- governance redesign
- promotion authority mutation
- freeform worker autonomy

## Required validation
- pytest
- deterministic certifier

## Acceptance criteria
- certifier check prevents bypass of contracts and reports for task > 96
- exempts legacy tasks <= 96

## Required execution discipline
READ-FIRST mandatory
Inspect actual files first
Use Serena when relevant
Treat ai_runtime/inbox controller requests as READ-ONLY
No implementation from memory
Return exact validation output
Separate evidence from assumptions

## State
APPROVED FOR IMPLEMENTATION

## Next
TASK XXX [TBD]
