# Authoritative AI Runtime Workflow

## 1. Overview
The `utility_automation_v2` repository enforces a strict, deterministic runtime governance loop for all AI agents and human operators. Every task progresses through cryptographic and deterministic CLI quality gates before code modification or promotion is authorized.

```
+-------------------------------------------------------------------------+
|                  CONTROLLER PLANE (Harness & Inbox)                     |
|  [Step 0] start_runtime_task.py                                         |
|    ├── 0.1 create_controller_request.py (Template & Placeholders Gate)  |
|    ├── 0.5 validate_controller_request.py (Structural Integrity Gate)   |
|    ├── 1.0 issue_execution_contract.py (Cryptographic Boundary Lock)    |
|    └── 2.0 check_execution_readiness.py (Pre-Execution Identity Gate)   |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     OBSERVABILITY & VISIBILITY                          |
|  [Step 2.5] inspect_runtime_contract.py (Continuous State Audit)        |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    WORKER EXECUTION DISCIPLINE                          |
|  [Step 3] Serena Repository Tools & Active Action Guard                 |
|    └── 3.0 enforce_runtime_action.py (Physical Read/Write/Cmd Block)    |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     EVIDENCE & VERIFICATION LOOP                        |
|  [Step 3.1] Generate Canonical Artifacts (Transcript, Trace, Report)    |
|  [Step 3.2] validate_runtime_artifact_bundle.py                         |
|  [Step 3.5] generate_completion_evidence.py (Deterministic Manifest)    |
|  [Step 4.0] validate_completion_evidence.py (Post-Completion Gate)      |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     PROMOTION & RELEASE ADVISORY                        |
|  [Step 5.0] Deterministic Mesh Certification & Promotion Gatekeeper     |
+-------------------------------------------------------------------------+
```

## 2. Mandatory Gate Execution Details

### Step 0: Controller Automation Harness (`start_runtime_task.py`)
The Controller harness automates the setup phase by orchestrating request generation, validation, contract issuance, and readiness checking in a single atomic command.
```bash
$env:PYTHONPATH="."; python src/tools/runtime/start_runtime_task.py \
    --task-id TASK-XXX --actor-id WORKER-01 \
    --request-file ai_runtime/inbox/TASK-XXX-controller-request.md \
    --allow-read src/ tests/ ai_runtime/ \
    --allow-write src/ ai_runtime/ tests/ \
    --expected-output src/tools/runtime/example.py
```

### Step 0.1 & 0.5: Request Generation and Validation
- **`create_controller_request.py`**: Generates structured markdown specifications without unresolved template placeholders (`[REPLACE]`, empty brackets).
- **`validate_controller_request.py`**: Ensures structural completeness and fail-closed blocking if placeholders are detected.

### Step 1.0: Contract Issuance (`issue_execution_contract.py`)
Generates a signed execution contract (`ai_runtime/contracts/{task_id}.json`) enforcing allowed read/write boundaries, shell command rules, and time expiration limits.

### Step 2.0: Readiness Verification (`check_execution_readiness.py`)
Verifies active contract validity, identity matching, and clean working tree status (`git status`). Execution stops immediately if unrelated uncommitted changes exist.

### Step 2.5: Lifecycle Inspection (`inspect_runtime_contract.py`)
Provides continuous observability across contract states: `ISSUANCE_PENDING`, `ACTIVE`, `EXPIRED`, `VALIDATED_COMPLETION`, or corrupt states.

### Step 3.0: Active Runtime Enforcement (`enforce_runtime_action.py`)
Execution wrappers query this gate before performing any physical read, write, or shell command execution on disk.

### Step 3.1 - 4.0: Evidence Provenance & Completion Gate
- **`validate_runtime_artifact_bundle.py`**: Verifies existence and schema validity of the execution transcript, tool trace, worker report, and validation output.
- **`generate_completion_evidence.py`**: Hashes actual outputs and execution trace into a canonical evidence manifest (`ai_runtime/reports/{task_id}-evidence.json`).
- **`validate_completion_evidence.py`**: Compares evidence against contract scope. Any unauthorized file writes or missing expected outputs result in immediate failure.

## 3. Reference
For the full technical CLI specification and argument schemas, reference `ai_runtime/governance/RUNTIME_WORKFLOW.md`.
