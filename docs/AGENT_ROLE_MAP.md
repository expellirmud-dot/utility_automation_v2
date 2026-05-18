# Authoritative Agent & Role Map

The deterministic governance platform relies on strict role separation and explicit authority boundaries. No single entity can autonomously specify, implement, validate, and promote changes.

```
+-----------------------------------------------------------------------+
|                      HUMAN LEAD / OPERATOR                            |
|  Sole authority for ledger state transitions and release signatures.  |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                     CONTROLLER (ChatGPT / Harness)                    |
|  Authorizes specifications in `ai_runtime/inbox/`.                    |
|  Executes `start_runtime_task.py` to issue cryptographic contracts.   |
|  Reviews uncommitted worker handoff packages before commit approval.  |
+-----------------------------------------------------------------------+
                                    |
                                    v (Cryptographic Contract)
+-----------------------------------------------------------------------+
|                 WORKER AGENT (Gemini CLI / Implementer)               |
|  Executes READ-FIRST repository inspection via Serena.                |
|  Confirms readiness and executes strictly within allowed path scopes.  |
|  Generates canonical evidence reports (`ai_runtime/reports/`).        |
|  Runs `pytest` and `deterministic_certifier.py` validation.           |
+-----------------------------------------------------------------------+
                                    |
                                    v (Validated Evidence Bundle)
+-----------------------------------------------------------------------+
|              PROMOTION GATEKEEPER & CERTIFICATION HARNESS             |
|  Executes deterministic mesh consensus checks across nodes.           |
|  Calculates immutable promotion bundle hashes.                        |
|  Enforces fail-closed blocking on non-certified implementations.      |
+-----------------------------------------------------------------------+
```

## 1. Core Responsibilities

### 1.1 Human Lead / Operator
- **Authority**: Ultimate governance authority.
- **Scope**: Approves major architectural directions, security policy updates, and production deployment authorization.
- **Constraints**: Enforces rule discipline in `AGENTS.md` and `PROJECT_RULES.md`.

### 1.2 Controller (ChatGPT / Orchestration Harness)
- **Authority**: Specification and contract authority.
- **Scope**: Authors controller requests (`create_controller_request.py`), runs quality validation (`validate_controller_request.py`), and issues execution contracts (`issue_execution_contract.py`).
- **Constraints**: Cannot directly modify implementation source code or bypass contract gates. Treats worker reports as review packages.

### 1.3 Worker Agent (Gemini CLI)
- **Authority**: Scoped execution and implementation authority.
- **Scope**: Implements assigned tasks, writes tests, validates changes, and produces deterministic completion evidence manifests (`generate_completion_evidence.py`).
- **Constraints**: AI is advisory only. Cannot self-approve commits or pushes. Cannot modify contract boundaries or unassigned files.

### 1.4 Promotion Gatekeeper (Automated Verification)
- **Authority**: Release eligibility authority.
- **Scope**: Executes `deterministic_certifier.py`, verifies evidence hashes against active contracts, and validates artifact bundle standardization (`validate_runtime_artifact_bundle.py`).
- **Constraints**: Fully deterministic. Zero tolerance for flaky tests, non-reproducible builds, or missing evidence files.
