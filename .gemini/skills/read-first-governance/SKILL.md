---
name: read-first-governance
description: Mandatory READ-FIRST workflow for utility_automation_v2 before implementation.
---

MISSION:
Perform READ-FIRST governance inspection only.

MODE:
READ-ONLY

MANDATORY READ ORDER:
1. repo_memory/project_state.json
2. repo_memory/architecture_map.md
3. repo_memory/known_landmines.md
4. repo_memory/task_registry.md
5. repo_memory/module_registry.md
6. repo_memory/validation_commands.md
7. PROJECT_RULES.md
8. AI_HANDOFF.md
9. AGENTS.md

SERENA:
Activate Serena at:
D:\utility_automation_v2

IF SERENA FAILS:
STOP.
Do not proceed from memory.

RULES:
- No implementation
- No file edits
- No speculative assumptions
- No fabricated inspection
- No inferred task specs
- No architecture invention

REQUIRED OUTPUT:
A. Serena activated? YES/NO
B. exact files inspected
C. exact task spec found? YES/NO
D. exact spec location
E. proposed scope
F. validation commands
G. governance risks
H. explicit statement: no code edited
