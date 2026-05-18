---
name: task-state-governance
description: Task continuity, repo memory, and next-task state discipline.
---

# Task State Governance

## Requirements

After implementation commit, update continuity artifacts when task is complete:

- AI_HANDOFF.md
- repo_memory/project_state.json
- repo_memory/task_registry.md
- repo_memory/task_progression.md

Use separated commit pattern:

1. implementation commit
2. continuity update commit

## State Rules

- do not invent task state
- do not fabricate validation
- report exact evidence
- current_completed_task and next_task must be consistent
