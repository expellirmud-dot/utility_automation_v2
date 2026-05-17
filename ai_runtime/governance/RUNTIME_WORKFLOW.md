# AI Runtime Workflow Governance

This document defines the mandatory operational gates for all AI workers operating within the `utility_automation_v2` repository.

## 1. PRE-IMPLEMENTATION REPOSITORY GATE
Before any code modification or file creation begins, the worker MUST pass the **Runtime Contract Guard**.

1. **Contract Verification**:
   - A valid `ExecutionContract` must exist in `ai_runtime/contracts/{TASK-ID}.json`.
   - The contract must be structurally sound, not expired, and match the current `task_id` and `worker_id`.
    - **Verification**: The `RuntimeContractGuard` service is the authoritative source for validating contracts. Workers are required to use this service to verify that the contract is present, valid, and covers the intended scope before beginning implementation.
2. **State Check**: Run `git status` to inspect the current working tree.
3. **Cleanliness Verification**:
   - The working tree must be clean of unrelated changes.
   - If modified files are present, they must be explicitly classified as belonging to the current task.
   - Any pre-existing "dirty" state must be reported to the controller.
4. **Stop Condition**: Stop execution immediately if the working tree is dirty with unrelated changes, unless explicit approval is granted by the controller.

## 2. IMPLEMENTATION DISCIPLINE
- Follow the `READ-FIRST` workflow.
- Adhere to strictly scoped changes.
- Use Serena for all repository operations.

## 3. POST-COMPLETION EVIDENCE GATE
Before declaring a task complete, the worker MUST provide a "Review Package" containing:
1. **Final State**: Current `git status` output.
2. **Change Evidence**: Exact `git diff` of the changes made.
3. **Validation Proof**: Exact output from the required test commands (e.g., `pytest`).
4. **Artifact Manifest**: A comprehensive list of all created or modified files.
5. **Proof of Existence**: Directory listings or file reads proving the output artifacts exist.

Failure to provide any of these components will result in the implementation being marked as "NOT CERTIFIED".
