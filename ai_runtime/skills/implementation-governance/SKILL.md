---
name: implementation-governance
description: Exact scoped implementation discipline for deterministic governance repository work.
---

# Implementation Governance

## Before Editing

Required:

1. Complete READ-FIRST.
2. Confirm clean tracked working tree.
3. Identify exact files to change.
4. State implementation plan.
5. State validation commands.

## Implementation Rules

Allowed:

- exact scoped implementation
- minimal diffs
- additive changes
- bounded adapters
- existing architecture reuse

Forbidden:

- implementation from memory
- speculative refactor
- broad UI redesign unless explicitly assigned
- arbitrary subprocess bridge from web/API payloads
- hidden operational defaults
- fake/dummy defaults such as dummy, Auto-generated, New Task, Operator triggered
- broad allowlists
- certifier weakening to make tests pass
- direct ledger, mesh, quorum, promotion, recovery, commit, or push authority

## After Editing

Return canonical review package:

1. final git status
2. exact changed files list
3. targeted git diffs
4. exact validation commands
5. raw validation output
6. evidence artifacts created
7. remaining risks
8. explicit no commit / no push statement unless commit was explicitly approved
