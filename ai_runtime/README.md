# AI Runtime Architecture & Folder Responsibilities

The `ai_runtime/` directory is the physical state layer for the governed AI execution loop in `utility_automation_v2`. It houses incoming task requests, cryptographic execution contracts, canonical evidence reports, and workflow governance definitions.

---

## 1. Directory Structure & Responsibilities

```
ai_runtime/
├── inbox/         # Authoritative read-only controller request specifications (*-controller-request.md).
├── contracts/     # Deterministic JSON execution contracts (*.json) defining read/write/cmd boundaries.
├── reports/       # Canonical runtime verification artifacts (transcripts, tool traces, evidence manifests).
├── governance/    # Core runtime workflow definitions (e.g. RUNTIME_WORKFLOW.md).
├── templates/     # Standardized templates for controller requests and worker reports.
├── skills/        # Reusable deterministic execution patterns and tool definitions.
├── decisions/     # Architectural decision records (ADRs) governing runtime evolution.
└── archive/       # Historical records of completed and archived runtime contracts.
```

---

## 2. The Governed Handoff Loop

Every runtime task strictly follows the governed lifecycle:

1. **Request Manifestation (`inbox/`)**: The Controller generates a fully instantiated request via `create_controller_request.py` and validates structural integrity via `validate_controller_request.py`.
2. **Contract Issuance (`contracts/`)**: An authoritative cryptographic execution contract is issued via `issue_execution_contract.py` specifying allowed read/write paths and duration limits.
3. **Pre-Execution Gate**: Worker verifies identity and clean repo state via `check_execution_readiness.py`.
4. **Execution Discipline**: Worker implements code using Serena tools. Actions are verified in real time via `enforce_runtime_action.py`.
5. **Evidence Generation (`reports/`)**: Worker records execution transcript, canonical JSON tool trace, worker report, and test validation output.
6. **Completeness & Integrity Check**: Worker validates bundle via `validate_runtime_artifact_bundle.py` and generates completion manifest via `generate_completion_evidence.py`.
7. **Completion Gate Validation**: Worker runs `validate_completion_evidence.py` to cryptographically verify evidence against the contract.
8. **Controller Review & Commit**: Worker presents uncommitted review package to the controller for commit approval.

---

## 3. Strict Operational Invariants

- **`inbox/` is READ-ONLY for Workers**: Workers must never modify or delete controller request files.
- **`contracts/` is Cryptographically Bound**: Active contract JSON files define exact execution boundaries and expiration times.
- **`reports/` Requires Canonical Formatting**: All artifacts must follow exact naming conventions (`{task_id}-evidence.json`, etc.) and conform to schema validators.
