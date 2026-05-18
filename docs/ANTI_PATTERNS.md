# Authoritative Governance Anti-Patterns

To maintain absolute determinism and cryptographic auditability within the `utility_automation_v2` platform, workers and controllers must strictly avoid the following anti-patterns.

---

## 1. Specification & Contract Anti-Patterns

### 1.1 Uninstantiated Placeholders
- **Anti-Pattern**: Submitting controller requests containing `[REPLACE]`, `REPLACE_WITH_TITLE`, or empty bracket placeholders.
- **Consequence**: Immediate fail-closed blocking by `validate_controller_request.py` (Step 0.5).
- **Correct Pattern**: Use `create_controller_request.py` to generate fully specified markdown artifacts.

### 1.2 Overbroad Scope Issuance
- **Anti-Pattern**: Issuing execution contracts with root-level wildcard write permissions (`--allow-write /`).
- **Consequence**: Undermines the principle of least privilege and increases risk of unintended state mutation.
- **Correct Pattern**: Explicitly restrict `--allow-write` and `--allow-read` to specific target directories (e.g. `src/tools/runtime/`).

---

## 2. Worker Execution Anti-Patterns

### 2.1 Implementation from Memory
- **Anti-Pattern**: Writing code or test logic without first inspecting actual repository state or reading `repo_memory/`.
- **Consequence**: Introduces subtle inconsistencies, redundant modules, or regressions.
- **Correct Pattern**: Execute a strict `READ-FIRST` inspection using Serena tools prior to any file modification.

### 2.2 Speculative Refactoring & Mixed Changes
- **Anti-Pattern**: Cleaning up unrelated code, re-formatting files, or upgrading dependencies outside the assigned task scope.
- **Consequence**: Fails the clean working tree gate (`git status`) and results in immediate rejection during contract evidence validation.
- **Correct Pattern**: Strictly confine modifications to the files listed in `--expected-output` and the active contract scope.

### 2.3 Autonomous Self-Approval
- **Anti-Pattern**: Committing and pushing code directly to remote branches without presenting an uncommitted review package to the controller.
- **Consequence**: Violates core governance rules (`AGENTS.md`).
- **Correct Pattern**: Present exact `git status`, `git diff`, and validation logs to the controller and await explicit commit approval.

---

## 3. Testing & Validation Anti-Patterns

### 3.1 Fabricated Validation Reports
- **Anti-Pattern**: Claiming that tests or deterministic certifications passed without executing the physical commands or reporting truncated/fake output.
- **Consequence**: Violates the Completion Evidence Gate.
- **Correct Pattern**: Run `python -m pytest -q` and `python src/tests/certification/deterministic_certifier.py` and capture the exact terminal output into `ai_runtime/reports/TASK-XXX-validation-output.txt`.

### 3.2 Non-Deterministic Test Design
- **Anti-Pattern**: Introducing tests that rely on external network requests, unseeded randomness, or exact real-time clock delays.
- **Consequence**: Causes flaky CI failures during mesh quorum certification.
- **Correct Pattern**: Use deterministic mocks, fixed time seeds, and stable ordering invariants.
