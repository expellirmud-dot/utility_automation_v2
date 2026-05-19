# Controller Execution Request

## Task ID
TASK-098

## Title
Runtime Governance History Reconciliation

## Authority
Draft controller request pending human/controller scope approval.

## Objective
Build a deterministic reconciliation report for runtime governance evidence covering TASK-071 through TASK-097, using TASK-097 as the gold sample for the current runtime workflow.

## Architectural rationale
TASK-097 established the post-baseline runtime governance enforcement model. TASK-098 reconciles historical runtime evidence without rewriting history, fabricating approvals, or treating missing runtime artifacts as implementation failures.

## Scope

### In scope
- Inspect actual runtime artifacts under `ai_runtime/inbox/`, `ai_runtime/contracts/`, and `ai_runtime/reports/`.
- Reconcile TASK-071 through TASK-097 in deterministic task-id order.
- Classify each task into exactly one runtime evidence category:
  1. full runtime evidence
  2. partial runtime evidence
  3. controller/contract only
  4. report only
  5. runtime evidence gap
- Separate inspected facts from assumptions.
- Classify missing runtime artifacts as historical governance evidence gaps only.
- Do not claim missing runtime artifacts mean implementation failed.
- Document approved mixed-state exceptions for TASK-088 and TASK-089 only if supported by repository context.
- Use TASK-097 as the gold sample for the required runtime workflow shape.
- Produce deterministic reconciliation artifacts only after controller approval.

### Current inventory facts
- `ai_runtime/inbox/` contains controller requests for TASK-071, TASK-088, TASK-089, TASK-097, and TASK-RUNTIME-002.
- `ai_runtime/contracts/` contains contracts for TASK-088, TASK-089, and TASK-097.
- `ai_runtime/reports/` contains runtime reports for TASK-071, TASK-075, TASK-076 through TASK-087, and TASK-097.
- Runtime evidence is missing or incomplete for TASK-072 through TASK-074.
- Runtime evidence is missing or incomplete for TASK-088 through TASK-096 except inbox/contracts for TASK-088/TASK-089 and full baseline evidence for TASK-097.
- Repository bootstrap context identifies TASK-088/TASK-089 untracked inbox and contract files as expected and allowed mixed-state files.

### Assumptions to verify during implementation
- Historical task implementation status must be derived only from repository evidence, not inferred from missing runtime artifacts.
- Runtime reconciliation can be completed as report/artifact generation without source-code changes unless controller explicitly expands scope.
- TASK-097 defines the complete runtime baseline evidence shape for future comparisons.

### Candidate artifacts
ai_runtime/reports/TASK-098-runtime-governance-history-reconciliation.md
ai_runtime/reports/TASK-098-evidence.json
ai_runtime/reports/TASK-098-worker-report.md
ai_runtime/reports/TASK-098-execution-transcript.md
ai_runtime/reports/TASK-098-tool-trace.json
ai_runtime/reports/TASK-098-validation-output.txt
ai_runtime/reports/TASK-098-runtime-manifest.json

### Runtime artifacts to inspect
ai_runtime/inbox/
ai_runtime/contracts/
ai_runtime/reports/
repo_memory/
PROJECT_RULES.md
AI_HANDOFF.md
AGENTS.md
CONTROLLER.md

### Tests
No source-code implementation is approved by this draft request.

If implementation remains artifact-only:
- python -m pytest -q
- $env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py

If source-code changes are later approved:
- Add or update targeted tests only within the approved controller scope.
- Run full validation required by AGENTS.md.

## Constraints
- Ledger remains sole source of truth.
- SQLite is projection/cache only.
- Mesh quorum remains the only authority for committed state transitions.
- AI is advisory only.
- Determinism is mandatory.
- Certification integrity must be preserved.
- No source-code edits are approved by this draft request.
- No runtime mutation APIs are approved by this draft request.
- No historical approval may be fabricated.
- No missing runtime evidence may be marked as passed.
- No missing runtime artifact may be treated as implementation failure.
- Runtime gaps must be classified as historical governance evidence gaps only.
- Facts and assumptions must be explicitly separated.

## Non-goals
- Implementing reconciliation code before approval.
- Backfilling missing historical approvals.
- Creating fabricated contracts, reports, transcripts, validation output, or tool traces for prior tasks.
- Reclassifying historical implementation status without repository evidence.
- Changing ledger, SQLite, mesh, quorum, promotion, replay, recovery, authentication, or trust authority.
- Adding dashboard mutation actions or control-plane flows.
- Committing without controller review.

## Required validation
- READ-FIRST report before implementation.
- Serena activation confirmation.
- Exact artifact inventory evidence.
- Deterministic reconciliation output review.
- python -m pytest -q
- $env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py

## Acceptance criteria
- TASK-071 through TASK-097 are listed in stable ascending task-id order.
- Each task has exactly one classification:
  - full runtime evidence
  - partial runtime evidence
  - controller/contract only
  - report only
  - runtime evidence gap
- Each classification cites concrete inspected artifacts.
- Missing or incomplete artifacts are labeled as historical governance evidence gaps only.
- TASK-088/TASK-089 mixed-state exceptions are documented only from repository-supported evidence.
- TASK-097 is documented as the gold sample for the current runtime workflow.
- Facts are separated from assumptions.
- No source-code files are changed unless separately approved.
- Final report includes exact git status, git diff, changed files, validation commands, validation outputs, artifact existence proof, and remaining risks.

## Required execution discipline
READ-FIRST mandatory.
Inspect actual files first.
Use Serena when relevant.
Treat `ai_runtime/inbox/` controller requests as READ-ONLY during implementation.
No implementation from memory.
No fabricated validation.
No fabricated approval.
Return exact validation output.
Separate evidence from assumptions.
Stop before implementation until controller approval is explicit.

## State
WAITING_GPT_REVIEW

## Next
Controller review and explicit approval or rejection of TASK-098 scope.

