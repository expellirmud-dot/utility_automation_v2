---
name: agent-run-governance
description: Governance rules for stateful agent runs, approval pauses, resumable workflows, and tool-call execution loops.
---

# Agent Run Governance

Use this skill when designing, running, reviewing, or modifying agent execution loops.

## Core Principles

- Agent runs are stateful execution workflows.
- Approval is a paused run, not a new independent task.
- Resume from preserved state after approval.
- No self-approval.
- No autonomous authority mutation.
- All tool calls must be auditable.

## Required Agent Run State

Track:

1. run id or response id
2. task id
3. current lifecycle state
4. pending approval state
5. tool calls requested
6. tool calls approved
7. tool results
8. failure state
9. resume state

## Approval Rules

Human approval is required for:

- write actions
- external side effects
- file mutations
- git operations
- runtime contract changes
- ledger/quorum/mesh/promotion/recovery actions
- sending external messages or data

## Forbidden

- treating approval as implied
- restarting from memory after pause
- hidden tool calls
- unlogged mutation
- autonomous commit/push
- autonomous promotion
- direct authority execution
- lossy run-state reconstruction

## Required Output

Return:

- current run state
- pending approval items
- allowed next action
- blocked actions
- audit trail status
- PASS/FAIL
