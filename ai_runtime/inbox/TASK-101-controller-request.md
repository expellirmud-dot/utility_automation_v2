# Controller Execution Request

## Task ID
TASK-101

## Title
TASK-101 — AI Tools Kit Bootstrap State Refresh

## Authority
Human-approved recommendation for refreshing bootstrap and state documentation after TASK-100.

## Objective
Refresh stale repository state, handoff, and bootstrap documentation after completed TASK-100. Create missing AI Tools Kit bootstrap/status documents as documentation scaffolds, mark TASK-100 as completed, and mark TASK-101 as the current active task.

## Architectural rationale
TASK-100 established the runtime governance baseline. Following its completion, the repository's bootstrap, handoff, and operating context files must be updated to align with the active baseline and prevent future agents from relying on stale task state. Creating documentation scaffolds for the AI Tools Kit ensures proper traceability and operational alignment.

## Scope

### In scope
- Refresh repository bootstrap/state documentation after completed TASK-100.
- Mark TASK-100 as completed and TASK-101 as the current active task in project state and task registry.
- Create missing AI Tools Kit bootstrap/status documents only as documentation scaffolds.
- Preserve the legacy untracked exception for TASK-088/TASK-089.
- Maintain all governance invariants and validation routines.

### Allowed files (Controller Request Phase)
- [TASK-101-controller-request.md](file:///d:/utility_automation_v2_light/ai_runtime/inbox/TASK-101-controller-request.md)

### Candidate Implementation Artifacts (Implementation Phase)
- [project_state.json](file:///d:/utility_automation_v2_light/repo_memory/project_state.json)
- [task_registry.md](file:///d:/utility_automation_v2_light/repo_memory/task_registry.md)
- [agent_bootstrap_prompt.txt](file:///d:/utility_automation_v2_light/repo_memory/agent_bootstrap_prompt.txt)
- [AI_HANDOFF.md](file:///d:/utility_automation_v2_light/AI_HANDOFF.md)
- [AI_OPERATING_CONTEXT.md](file:///d:/utility_automation_v2_light/AI_OPERATING_CONTEXT.md)
- [SESSION_BOOTSTRAP.md](file:///d:/utility_automation_v2_light/SESSION_BOOTSTRAP.md)
- [AI_TOOLS_KIT_STATUS.md](file:///d:/utility_automation_v2_light/AI_TOOLS_KIT_STATUS.md)
- [WORKFLOW_GUIDE.md](file:///d:/utility_automation_v2_light/WORKFLOW_GUIDE.md)
- [AI_ORG_ARCHITECTURE.md](file:///d:/utility_automation_v2_light/AI_ORG_ARCHITECTURE.md)
- [RUNTIME_MATRIX.md](file:///d:/utility_automation_v2_light/RUNTIME_MATRIX.md)
- [TOOL_MATRIX.md](file:///d:/utility_automation_v2_light/TOOL_MATRIX.md)
- [NEXT_ACTIONS.md](file:///d:/utility_automation_v2_light/NEXT_ACTIONS.md)
- [README.md](file:///d:/utility_automation_v2_light/README.md)
- [TASK-101.json](file:///d:/utility_automation_v2_light/ai_runtime/contracts/TASK-101.json)
- [TASK-101-worker-report.md](file:///d:/utility_automation_v2_light/ai_runtime/reports/TASK-101-worker-report.md)
- [TASK-101-execution-transcript.md](file:///d:/utility_automation_v2_light/ai_runtime/reports/TASK-101-execution-transcript.md)
- [TASK-101-tool-trace.json](file:///d:/utility_automation_v2_light/ai_runtime/reports/TASK-101-tool-trace.json)
- [TASK-101-validation-output.txt](file:///d:/utility_automation_v2_light/ai_runtime/reports/TASK-101-validation-output.txt)
- [TASK-101-runtime-manifest.json](file:///d:/utility_automation_v2_light/ai_runtime/reports/TASK-101-runtime-manifest.json)

## Constraints
- No source code edits.
- No runtime behavior changes.
- No certifier or governance enforcement changes.
- Do not modify `runtime_task_governance_checks.py`.
- No TASK-088/TASK-089 cleanup.
- Do not mark TASK-101 as completed.
- Do not set next_task to TASK-102.
- Do not define or recommend TASK-102.
- TASK-101 contract applies only to TASK-101.
- All JSON artifacts must be parseable JSON only, no Markdown.
- Runtime manifest must include SHA256 hashes for primary artifacts.
- During controller request phase: stop after creating controller request.
- During implementation phase: implement only approved candidate artifacts.
- Do not commit before GPT/controller review.

## Non-goals
- Modifying core runtime execution behavior or code.
- Defining tasks beyond TASK-101 (e.g., TASK-102).
- Cleaning up untracked legacy files for TASK-088/TASK-089.
- Backfilling historical evidence records for prior tasks.

## Required validation
- `git status`
- `git diff`
- `python -m pytest -q`
- `$env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py`

## Acceptance criteria
- [TASK-101-controller-request.md](file:///d:/utility_automation_v2_light/ai_runtime/inbox/TASK-101-controller-request.md) exists in the inbox.
- Project memory registers TASK-100 as completed and TASK-101 as the current active task only.
- Bootstrap and state documentation files are updated with accurate references.
- Missing status/bootstrap documents are initialized as scaffolds.
- The legacy exceptions for TASK-088/TASK-089 remain untouched.
- TASK-101 remains current active task until final controller review and commit approval.
- TASK-102 is not defined or recommended anywhere.
- All JSON artifacts are valid parseable JSON with no Markdown content.
- Runtime manifest includes SHA256 hashes for primary TASK-101 artifacts.

## Required execution discipline
READ-FIRST mandatory.
Serena activation mandatory.
Inspect actual files first.
No implementation from memory.
No source code edits.
No runtime behavior changes.
No TASK-088/TASK-089 cleanup.
No fabricated validation.
No fabricated approval.
Return exact validation output.
Stop before commit unless controller explicitly approves commit.

## State
WAITING_GPT_REVIEW

## Next
Controller approval or rejection of TASK-101 implementation scope.

