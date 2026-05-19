# Controller Execution Request

## Task ID
TASK-099

## Title
Runtime State Synchronization After TASK-098

## Authority
Human-approved narrowed controller request scope.

## Objective
Synchronize repository state and handoff documentation after completed TASK-098 runtime governance history reconciliation.

## Architectural rationale
TASK-098 completed runtime governance history reconciliation. Repository state and handoff documents must be synchronized so future agents start from actual repository state instead of stale task pointers.

## Scope

### In scope
- Inspect current TASK-098 runtime artifacts.
- Mark TASK-098 as completed and TASK-099 as current active task only.
- Preserve documented TASK-088/TASK-089 mixed-state legacy exception.
- Preserve all governance invariants and validation instructions.
- Produce TASK-099 runtime evidence artifacts.

### Allowed files
- repo_memory/project_state.json
- repo_memory/task_registry.md
- repo_memory/agent_bootstrap_prompt.txt
- AI_HANDOFF.md
- ai_runtime/inbox/TASK-099-controller-request.md
- ai_runtime/reports/TASK-099-worker-report.md
- ai_runtime/reports/TASK-099-execution-transcript.md
- ai_runtime/reports/TASK-099-tool-trace.json
- ai_runtime/reports/TASK-099-validation-output.txt
- ai_runtime/reports/TASK-099-runtime-manifest.json

## Constraints
- No source code edits.
- No runtime behavior changes.
- No TASK-088/TASK-089 cleanup.
- Do not define TASK-100.
- Do not create TASK-100 controller request, contract, report, registry entry, handoff note, or next-task recommendation.
- Do not backfill missing historical runtime evidence.
- Do not fabricate approvals, validation output, reports, contracts, transcripts, manifests, or tool traces.
- Do not change ledger, SQLite, mesh, quorum, promotion, replay, recovery, authentication, trust, or authority semantics.
- TASK-088/TASK-089 untracked mixed-state legacy exception remains intentionally untracked unless separately approved.

## Non-goals
- Implementing source-code behavior.
- Changing runtime governance enforcement behavior.
- Cleaning up TASK-088/TASK-089 mixed-state files.
- Defining future TASK-100 scope.
- Backfilling historical runtime artifacts.
- Redesigning repository memory, handoff, or runtime workflow.

## Required validation
- git status
- git diff
- python -m pytest -q
- $env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py

## Acceptance criteria
- `repo_memory/project_state.json` identifies TASK-098 as completed and TASK-099 as current active task only.
- `repo_memory/task_registry.md` records TASK-098 completion and TASK-099 as current active task only.
- `repo_memory/agent_bootstrap_prompt.txt` no longer points agents at stale TASK-096/TASK-097 state.
- `AI_HANDOFF.md` reflects TASK-098 completion and TASK-099 as current active task only.
- TASK-100 is not defined anywhere by this task.
- TASK-088/TASK-089 untracked mixed-state files are not modified, moved, staged, deleted, or cleaned up.
- No source-code files are changed.
- Final report separates facts from assumptions and includes exact validation output.

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
Controller approval or rejection of TASK-099 implementation scope.
