# AI Runtime Workflow Governance

This document defines the mandatory operational gates for all AI workers operating within the `utility_automation_v2` repository.

## 1. PRE-IMPLEMENTATION REPOSITORY GATE
Before any code modification or file creation begins, the worker MUST perform the following:
1. **State Check**: Run `git status` to inspect the current working tree.
2. **Cleanliness Verification**:
   - The working tree must be clean of unrelated changes.
   - If modified files are present, they must be explicitly classified as belonging to the current task.
   - Any pre-existing "dirty" state must be reported to the controller.
3. **Stop Condition**: Stop execution immediately if the working tree is dirty with unrelated changes, unless explicit approval is granted by the controller.

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
