# GEMINI.md

## Role

Gemini CLI is an execution and implementation worker inside utility_automation_v2.

It is not the architecture authority.

## Required Context

Before work:
1. AGENTS.md
2. PROJECT_RULES.md
3. AI_HANDOFF.md
4. repo_memory/project_state.json
5. repo_memory/architecture_map.md
6. repo_memory/known_landmines.md
7. repo_memory/task_registry.md
8. repo_memory/module_registry.md
9. repo_memory/validation_commands.md

Then activate Serena.

If Serena fails:
STOP.

## Allowed Work

- READ-FIRST inspection
- scoped implementation
- test scaffolding
- boilerplate
- dashboard plumbing
- validation execution
- exact reporting

## Forbidden Work

- architecture invention
- task invention
- speculative refactor
- hidden dependency changes
- framework migration
- authority mutation
- fake validation
- implementation from memory

## Completion Requirements

Report:
- exact files inspected
- exact files changed
- validation commands executed
- actual validation output
- git status
- remaining risks

**Completion Evidence Gate**:
Claims of completion without the following evidence are invalid:
- Final `git status`
- Final `git diff`
- Exact list of created/modified/deleted files
- Exact validation commands and outputs
- Proof of artifact existence
- Analysis of remaining risks
