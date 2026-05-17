# Controller Request Template

## Task ID
TASK-XXX

## State
DRAFT

Allowed states:
DRAFT
READ_FIRST
WAITING_GPT_REVIEW
APPROVED_FOR_IMPLEMENTATION
IMPLEMENTED
VALIDATED
BLOCKED
ARCHIVED

## Goal
Describe the objective.

## Scope
Explicit scope only.

## State handling rules
- If State = DRAFT: perform READ-FIRST only unless implementation is explicitly approved.
- If State = WAITING_GPT_REVIEW: do not implement.
- If State = APPROVED_FOR_IMPLEMENTATION: implement only approved scope.
- If State = VALIDATED or ARCHIVED: do not rerun unless FORCE_RERUN = YES.
- If task was previously completed, report existing artifacts instead of repeating work.

## Required evidence artifacts
Worker must write:
- ai_runtime/reports/TASK-XXX-worker-report.md
- ai_runtime/reports/TASK-XXX-execution-transcript.md
- ai_runtime/reports/TASK-XXX-tool-trace.json

## Required workflow
- READ-FIRST
- Use Serena when relevant
- inspect actual files
- exact reporting
- preserve evidence trail

## Forbidden
- no implementation from memory
- no speculative redesign
- no fake validation
- no hidden edits
