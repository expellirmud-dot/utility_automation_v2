# AI Runtime Workflow Governance

This document defines the mandatory operational gates for all AI workers operating within the `utility_automation_v2` repository.

## Exact Runtime CLI Sequence

The runtime contract lifecycle is enforced at CLI gate points. Every task must strictly adhere to the established lifecycle:

```
+------------------------------------+
| 0.1 create_controller_request      |  (Request Template Generator)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 0.5 validate_controller_request    |  (Request Quality Gate)
+------------------------------------+
                  |
                  v
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
| 2.5 inspect_runtime_contract       |  (Lifecycle Visibility)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 3. worker execution                |  (Implementation Discipline)
|    -> enforce_runtime_action       |  (Active Action Gate)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 3.1 generate runtime evidence      |  (Artifact Manifestation)
|     artifacts                      |
+------------------------------------+
                  |
                  v
+------------------------------------+
| 3.2 validate artifact bundle       |  (Completeness Validator)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 3.5 generate completion evidence   |  (Evidence Provenance Manifest)
+------------------------------------+
                  |
                  v
+------------------------------------+
| 4. validate completion evidence    |  (Post-Completion Gate)
+------------------------------------+
```

### Step 0.1: Controller Request Generation (`create_controller_request`)
The Controller generates a fully instantiated controller request markdown file prior to validation and contract issuance. This tool prevents manual copy-paste errors and unresolved template placeholders.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/create_controller_request.py \
    --task-id TASK-XXX \
    --title "Sample Task Title" \
    --objective "Sample objective" \
    --rationale "Sample rationale" \
    --scope "Scope item 1" "Scope item 2" \
    --candidate-modules "src/main.py" \
    --tests "tests/test_main.py" \
    --validation "Validation item 1" \
    --acceptance "Acceptance item 1"
```
- **Output**: Canonical JSON success report and generated markdown at `ai_runtime/inbox/TASK-XXX-controller-request.md`.
- **Behavior**: Verifies generated output against internal quality gates. Fail-closed if required arguments are missing or if any placeholder is introduced.

### Step 0.5: Controller Request Validation (`validate_controller_request`)
Before an execution contract can be issued, the Controller or execution harness MUST validate the controller request markdown artifact for structural completeness and absence of uninstantiated template placeholders.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_controller_request.py \
    --request-file ai_runtime/inbox/TASK-XXX-controller-request.md
```
- **Output**: Deterministic JSON validation report (`{"is_valid": true, ...}`).
- **Behavior**: Exits with code 1 if required sections are missing or if uninstantiated placeholders (`[REPLACE]`, `REPLACE_`, empty brackets) are detected.

### Step 1: Contract Issuance (`issue_execution_contract`)
The Controller issues a deterministic execution contract specifying allowed read/write boundaries and expected outputs before assigning work to a worker.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/issue_execution_contract.py \
    --task-id TASK-XXX \
    --actor-id WORKER-01 \
    --allow-read src/ tests/ ai_runtime/ \
    --allow-write src/tools/runtime/ ai_runtime/ \
    --expected-output src/tools/runtime/enforce_runtime_action.py \
    --duration-mins 60
```
- **Output**: Canonical JSON representing the signed contract stored at `ai_runtime/contracts/{TASK-ID}.json`.
- **Behavior**: Fail-closed if required arguments or boundaries are omitted.

### Step 2: Worker Readiness Gate (`check_execution_readiness`)
Before any code modification or file creation begins, the worker MUST verify that a valid contract is active and matches their identity.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/check_execution_readiness.py \
    --task-id TASK-XXX \
    --actor-id WORKER-01
```
- **Output**: Deterministic JSON readiness result (`{"is_allowed": true, ...}`).
- **Behavior**: Exits with code 1 if the contract is missing, expired, or identity mismatches.
- **State Verification**: Worker must also run `git status` to verify a clean working tree. Stop execution immediately if the working tree is dirty with unrelated changes.

### Step 2.5: Runtime Contract Lifecycle Inspection (`inspect_runtime_contract`)
At any point during or after execution, execution harnesses or auditors can query the active contract to audit its lifecycle state (e.g. `ISSUANCE_PENDING`, `ACTIVE`, `EXPIRED`, `VALIDATED_COMPLETION`).

```bash
$env:PYTHONPATH="."; python src/tools/runtime/inspect_runtime_contract.py \
    --task-id TASK-XXX
```
- **Output**: Deterministic JSON detailing contract state, completeness reports, and completion evidence validity.
- **Behavior**: Returns non-error exit code 0 to allow continuous observability across all lifecycle states.

### Step 3: Implementation Discipline (`worker execution`)
- Follow the `READ-FIRST` workflow.
- Adhere strictly to the contract scope. Any unauthorized writes in the execution trace will be blocked during completion validation.
- Use Serena for repository operations.

### Step 3.0: Active Runtime Action Enforcement (`enforce_runtime_action`)
During implementation, execution harnesses and wrappers MUST query the contract before performing any physical action (read, write, or command execution) on the repository.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/enforce_runtime_action.py \
    --task-id TASK-XXX \
    --actor-id WORKER-01 \
    --action-type write \
    --path src/main.py
```
- **Output**: Deterministic JSON action validation result (`{"is_allowed": true, ...}`).
- **Behavior**: Exits with code 1 if the action violates allowed paths, forbidden patterns, or command rules specified in the active contract.

### Step 3.1: Generate Runtime Evidence Artifacts
Upon completing task execution, the worker documents runtime activity using established reporting conventions:
- **Execution Transcript**: Markdown log of the sequence of actions (`ai_runtime/reports/TASK-XXX-execution-transcript.md`).
- **Tool Trace**: Canonical JSON log of tools executed (`ai_runtime/reports/TASK-XXX-tool-trace.json`).
- **Worker Report**: Summary report (`ai_runtime/reports/TASK-XXX-worker-report.md`).
- **Validation Output**: Terminal test execution log (`ai_runtime/reports/TASK-XXX-validation-output.txt`).

### Step 3.2: Artifact Bundle Validation (`validate_runtime_artifact_bundle`)
The worker validates that all canonical runtime artifacts exist, follow correct naming conventions, and adhere strictly to mandatory templates and schemas.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_runtime_artifact_bundle.py \
    --task-id TASK-XXX \
    --reports-dir ai_runtime/reports \
    --generate-manifest
```
- **Output**: Deterministic JSON completeness and standardization validation report (`{"is_valid": true, "manifest": {...}}`).
- **Behavior**: Fail-closed if any artifact is missing, incorrectly named, or fails schema/template structure validation.

### Step 3.5: Evidence Manifest Generation (`generate_completion_evidence`)
The worker compiles raw runtime artifacts into a canonical, deterministically hashed `CompletionEvidence` manifest.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/generate_completion_evidence.py \
    --contract-id CONT-1234 \
    --worker-id WORKER-01 \
    --tool-trace-file ai_runtime/reports/TASK-XXX-tool-trace.json \
    --execution-transcript ai_runtime/reports/TASK-XXX-execution-transcript.md \
    --worker-report ai_runtime/reports/TASK-XXX-worker-report.md \
    --actual-output src/tools/runtime/enforce_runtime_action.py \
    --output-file ai_runtime/reports/TASK-XXX-evidence.json
```
- **Output**: Canonical JSON `CompletionEvidence` with computed `evidence_hash`.
- **Behavior**: Verifies physical existence of all actual outputs on disk. Fail-closed if outputs are missing or trace files are malformed.

### Step 4: Completion Validation Gate (`validate_completion_evidence`)
Before declaring a task complete, the worker MUST validate the generated evidence manifest against the authoritative execution contract.

```bash
$env:PYTHONPATH="."; python src/tools/runtime/validate_completion_evidence.py \
    --task-id TASK-XXX \
    --evidence-file ai_runtime/reports/TASK-XXX-evidence.json
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
