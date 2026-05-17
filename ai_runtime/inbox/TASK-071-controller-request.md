# Controller Execution Request

## Task ID
TASK-071

## Title
Governance Execution Contract Layer

## Authority
Human-approved controller request

## Objective
Implement a deterministic governance execution contract layer between controller decisions and worker execution.

## Architectural rationale
Current runtime flow allows ambiguity between controller intent and worker execution.

TASK 071 formalizes:

Controller Decision
→ Execution Contract
→ Runtime Inbox Request
→ Worker Execution
→ Validation Evidence
→ Completion Record

This preserves:
- deterministic governance
- auditability
- replayability
- authority boundaries

## Scope

### In scope
- deterministic execution contract models
- execution scope / constraints models
- execution contract serializer
- execution contract validator
- contract builder
- completion evidence validation
- fail-closed enforcement
- deterministic tests

### Candidate modules
src/services/governance/execution_contract/
  execution_contract_models.py
  execution_contract_builder.py
  execution_contract_validator.py
  execution_contract_serializer.py
  execution_contract_exceptions.py

### Runtime artifacts
ai_runtime/contracts/
ai_runtime/completions/

### Tests
tests/test_execution_contract_models.py
tests/test_execution_contract_validator.py
tests/test_execution_contract_builder.py
tests/test_execution_contract_fail_closed.py

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
- autonomous agent orchestration
- scheduler design
- governance redesign
- promotion authority mutation
- freeform worker autonomy

## Required validation
- deterministic serialization
- fail-closed invalid contracts
- scope boundary enforcement
- evidence completeness validation
- replay consistency

## Acceptance criteria
- execution contract models implemented
- validator blocks invalid contracts
- worker cannot exceed declared scope
- evidence validation works
- deterministic tests pass

## Required execution discipline
READ-FIRST mandatory
Inspect actual files first
Use Serena when relevant
No implementation from memory
Return exact validation output
Separate evidence from assumptions

## State
APPROVED FOR IMPLEMENTATION
