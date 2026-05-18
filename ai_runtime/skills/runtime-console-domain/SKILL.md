---
name: runtime-console-domain
description: Domain memory for utility_automation_v2_light runtime operator console tasks.
---

# Runtime Console Domain

Use this skill for runtime operator console work.

## Completed Runtime Console Arc

- TASK-087: read-only runtime web operator console foundation
- TASK-088: bounded runtime operator actions: create, start, finish
- TASK-089: controlled React forms replacing window.prompt
- TASK-090: live observability, polling, progress, sync state
- TASK-091: task templates / quick launch UX

## Current Console Capabilities

- task list
- task inspect/detail modal
- create task
- start task
- finish task
- form validation
- task templates
- live polling
- lifecycle/progress display

## Invariants

Preserve:
- existing GET inspection behavior
- explicit create/start/finish actions only
- typed backend client functions
- fail-closed validation
- human manual review before submit

Forbidden:
- new authority actions
- generic action selector
- generic runtime dispatcher
- direct ledger/mesh/quorum mutation
- approve/commit/push from UI
- backend mutation expansion without controller approval
