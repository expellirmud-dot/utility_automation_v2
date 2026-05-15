---
name: read-first-governance
description: Mandatory READ-FIRST workflow for utility_automation_v2 before implementation.
---

Rules:
1. Read:
- repo_memory/project_state.json
- repo_memory/architecture_map.md
- repo_memory/known_landmines.md
- repo_memory/task_registry.md
- repo_memory/module_registry.md
- repo_memory/validation_commands.md
- PROJECT_RULES.md
- AI_HANDOFF.md
- AGENTS.md

2. Activate Serena:
D:\utility_automation_v2

3. If Serena activation fails:
STOP

4. Do not implement from memory.

5. Return:
- files read
- spec found?
- exact spec location
- proposed scope
- validation commands
- governance risks
- explicit no code edited statement