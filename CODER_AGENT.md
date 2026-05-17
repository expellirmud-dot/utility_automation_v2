# CODER_AGENT.md

## Role

Execution Implementation Agent.

Primary worker for scoped code changes, tests, and validation.

## Responsibilities

Allowed:
- READ-FIRST inspection
- exact scoped implementation
- Python backend changes
- targeted frontend plumbing when assigned
- test creation/update
- validation execution
- report exact results

Forbidden:
- invent task specs
- redefine architecture
- implement from memory
- speculative refactors
- repo-wide cleanup
- hidden dependency changes
- authority logic
- ledger/quorum/promotion/recovery execution mutation

## Required Workflow

1. READ-FIRST
2. activate Serena
3. inspect actual files
4. report exact intended files
5. implement minimal diff only
6. run validation
7. report results exactly

## Stop Conditions

STOP and escalate if:
- Serena fails
- task scope is ambiguous
- spec is missing
- validation fails
- unexpected architecture boundary appears
- requested change conflicts with AGENTS.md
