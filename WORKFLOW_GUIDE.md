# AI Workflow Guide

Last Updated: 2026-05-20

## Objective
This guide provides developers and agent runtimes with clear operational rules for working on the `utility_automation_v2_light` project.

## Workflow Phases

### Phase 1: Pre-Implementation (READ-FIRST)
1. Always complete a full read of the latest handoff package [AI_HANDOFF.md](file:///d:/utility_automation_v2_light/AI_HANDOFF.md) and state database [project_state.json](file:///d:/utility_automation_v2_light/repo_memory/project_state.json).
2. Inspect the active task spec in `ai_runtime/inbox/`.
3. Check `git status` to ensure clean working tree boundaries.

### Phase 2: Implementation
1. Perform additive and scoped modifications only.
2. Minimize file diffs.
3. Reuse existing architecture patterns (ledger, SQLite projections, mesh orchestrators).
4. Do not make speculative refactors or clean up unrelated directories.

### Phase 3: Post-Implementation Validation
1. Execute validation checks before any commit.
2. Generate required runtime reports in `ai_runtime/reports/`.
3. Stop execution and wait for review before committing code.
