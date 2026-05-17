# AI Runtime Workflow Governance

This document defines the mandatory operational gates for all AI workers operating within the `utility_automation_v2` repository.

## Exact Runtime CLI Sequence

The runtime contract lifecycle is enforced at CLI gate points. Every task must strictly adhere to the four-step lifecycle:

```
+------------------------------------+
| 1. issue_execution_contract        |  (Controller Plane)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 2. check_execution_readiness       |  (Pre-Implementation Gate)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 3. worker execution                |  (Implementation Discipline)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 4. validate_completion_evidence    |  (Post-Completion Gate)
+------------------------------------+
```

### Step 1: Contract Issuance (`issue_execution_contract`)
The Controller issues a deterministic execution contract specifying allowed read/write boundaries and expected outputs before assigning work to a worker.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/issue_execution_contract.py \
    --task-id TASK-074 \
    --actor-id WORKER-01 \
    --allow-read src/ tests/ ai_runtime/ \
    --allow-write src/tools/runtime/ ai_runtime/ \
    --expected-output src/tools/runtime/issue_execution_contract.py \
    --duration-mins 60
```
- **Output**: Canonical JSON representing the signed contract stored at `ai_runtime/contracts/{TASK-ID}.json`.
- **Behavior**: Fail-closed if required arguments or boundaries are omitted.

### Step 2: Worker Readiness Gate (`check_execution_readiness`)
Before any code modification or file creation begins, the worker MUST verify that a valid contract is active and matches their identity.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/check_execution_readiness.py \
    --task-id TASK-074 \
    --actor-id WORKER-01
```
- **Output**: Deterministic JSON readiness result (`{"is_allowed": true, ...}`).
- **Behavior**: Exits with code 1 if the contract is missing, expired, or identity mismatches.
- **State Verification**: Worker must also run `git status` to verify a clean working tree. Stop execution immediately if the working tree is dirty with unrelated changes.

### Step 3: Implementation Discipline (`worker execution`)
- Follow the `READ-FIRST` workflow.
- Adhere strictly to the contract scope. Any unauthorized writes in the execution trace will be blocked during completion validation.
- Use Serena for repository operations.

### Step 4: Completion Validation Gate (`validate_completion_evidence`)
Before declaring a task complete, the worker MUST produce a `CompletionEvidence` JSON manifest and validate it against the execution contract.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_completion_evidence.py \
    --task-id TASK-074 \
    --evidence-file ai_runtime/reports/TASK-074-evidence.json
```
- **Output**: Canonical JSON validation report (`{"is_valid": true, ...}`).
- **Behavior**: Exits with code 1 if any expected output is missing or if any unauthorized write occurred in the execution trace.

---

## Post-Completion Evidence Package
Upon passing the validation gate, the worker presents the final review package containing:
1. **Final State**: Current `git status` output.
2. **Change Evidence**: Exact `git diff` of the changes made.
3. **Validation Proof**: Exact output from required test commands (`pytest` and `deterministic_certifier.py`).
4. **Artifact Manifest**: Comprehensive list of created/modified files.

Failure to pass any CLI gate or provide completion evidence results in the implementation being marked as **NOT CERTIFIED**.
