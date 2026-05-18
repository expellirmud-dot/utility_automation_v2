# Operator & Agent Quickstart Guide

This guide provides immediate, actionable steps for human operators, controllers, and AI workers to interact with the `utility_automation_v2` governed runtime platform.

---

## 1. Controller / Operator: Starting a New Task

To instantiate a new governed task from an approved specification, use the single-command automation harness:

```bash
# Start a runtime task by providing a controller request markdown file
$env:PYTHONPATH="."; python src/tools/runtime/start_runtime_task.py \
    --task-id TASK-085 \
    --actor-id WORKER-01 \
    --request-file ai_runtime/inbox/TASK-085-controller-request.md \
    --allow-read src/ tests/ ai_runtime/ docs/ repo_memory/ \
    --allow-write src/ ai_runtime/ tests/ \
    --expected-output src/services/new_feature.py
```
> **What happens**: The harness validates the request file (checking for placeholders), issues the cryptographic execution contract at `ai_runtime/contracts/TASK-085.json`, and verifies worker readiness.

---

## 2. Auditor / Observer: Inspecting Contract State

At any point during execution, check the status of a contract and its associated completion evidence:

```bash
$env:PYTHONPATH="."; python src/tools/runtime/inspect_runtime_contract.py \
    --task-id TASK-085
```
> **Output states**: `ISSUANCE_PENDING` -> `ACTIVE` -> `VALIDATED_COMPLETION` (or `EXPIRED`).

---

## 3. Worker: Pre-Implementation Checklist

Before modifying any code, every AI worker **MUST**:
1. Run `git status` to verify a clean working tree. **STOP** if dirty.
2. Read `repo_memory/project_state.json` and `repo_memory/task_registry.md`.
3. Verify readiness against the active contract:
   ```bash
   $env:PYTHONPATH="."; python src/tools/runtime/check_execution_readiness.py \
       --task-id TASK-085 --actor-id WORKER-01
   ```

---

## 4. Worker: Active Implementation & Tooling

During implementation:
- Use Serena repository tools for all file inspections and modifications.
- Active wrappers will enforce boundaries via `enforce_runtime_action.py`.

---

## 5. Worker: Post-Execution Verification & Evidence Bundle

Once code changes are complete:

### Step A: Run Repository Validation
```bash
python -m pytest -q
$env:PYTHONPATH="."; python src/tests/certification/deterministic_certifier.py
```

### Step B: Generate Canonical Runtime Reports
Save the following exact files in `ai_runtime/reports/`:
- `TASK-085-execution-transcript.md`
- `TASK-085-tool-trace.json`
- `TASK-085-worker-report.md`
- `TASK-085-validation-output.txt`

### Step C: Validate Artifact Bundle
```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_runtime_artifact_bundle.py \
    --task-id TASK-085 --reports-dir ai_runtime/reports --generate-manifest
```

### Step D: Generate Completion Evidence Manifest
```bash
$env:PYTHONPATH="."; python src/tools/runtime/generate_completion_evidence.py \
    --contract-id CONT-XXXX --worker-id WORKER-01 \
    --tool-trace-file ai_runtime/reports/TASK-085-tool-trace.json \
    --execution-transcript ai_runtime/reports/TASK-085-execution-transcript.md \
    --worker-report ai_runtime/reports/TASK-085-worker-report.md \
    --actual-output src/services/new_feature.py \
    --output-file ai_runtime/reports/TASK-085-evidence.json
```

### Step E: Run Completion Validation Gate
```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_completion_evidence.py \
    --task-id TASK-085 --evidence-file ai_runtime/reports/TASK-085-evidence.json
```

---

## 6. Worker: Controller Handoff & Commit Approval

Present the uncommitted review package to the controller with:
1. Exact `git status` and `git diff`.
2. Exact test and certifier output logs.
3. List of created/modified files.

**DO NOT COMMIT OR PUSH** until explicit controller approval is granted.
