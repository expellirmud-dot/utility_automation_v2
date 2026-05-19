# Session Bootstrap sequence

Last Updated: 2026-05-20

## Objective
This document outlines the step-by-step sequence required to safely bootstrap an active AI engineering session within `utility_automation_v2_light`.

## Bootstrap Procedure

1. **Read Repository Constraints First**:
   Read the mandatory project governance guidelines:
   - [PROJECT_RULES.md](file:///d:/utility_automation_v2_light/PROJECT_RULES.md)
   - [AGENTS.md](file:///d:/utility_automation_v2_light/AGENTS.md)
   - [AI_HANDOFF.md](file:///d:/utility_automation_v2_light/AI_HANDOFF.md)
   - [AI_OPERATING_CONTEXT.md](file:///d:/utility_automation_v2_light/AI_OPERATING_CONTEXT.md)

2. **Verify Working Tree Cleanliness**:
   Ensure `git status` reveals a clean working tree. The only permitted exceptions are the mixed-state untracked files defined in [agent_bootstrap_prompt.txt](file:///d:/utility_automation_v2_light/repo_memory/agent_bootstrap_prompt.txt).

3. **Activate Serena Project Context**:
   Verify Serena is active and indexing the path `D:\utility_automation_v2_light`. If Serena is not active, stop and resolve the activation failure.

4. **Verify Project Memories**:
   List active project memories via Serena:
   - `architecture`
   - `coding_rules`
   - `invariants`
   - `ui_rules`

5. **Run Baseline Tests**:
   Before modifying any files, execute the baseline tests to confirm safety:
   - `python -m pytest -q`
   - `$env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py`
