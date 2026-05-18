# Persistent Repository Memory (`repo_memory/`)

The `repo_memory/` directory provides persistent, repository-local memory and architectural context for AI implementation agents. It acts as an advisory synchronization layer between human operators, controllers, and workers.

---

## 1. Mandatory Read Order

Before initiating any implementation work, AI workers **MUST** read the following files in exact sequence:

1. **`project_state.json`**: Current project metadata, completed task pointer, next task pointer, and core invariants.
2. **`task_registry.md`**: Complete historical list of completed tasks and upcoming task definitions.
3. **`task_progression.md`**: High-level status of major architectural slices (e.g. Promotion Governance, Runtime Execution Guard).
4. **`architecture_map.md`**: Core component boundaries, data flow, and architectural invariants.
5. **`module_registry.md`**: Inventory of active service modules and their physical paths.
6. **`known_landmines.md`**: Documented system gotchas, security vulnerabilities, and anti-patterns.
7. **`validation_commands.md`**: Standardized CLI commands required for testing and deterministic certification.

---

## 2. Supporting Inventory Files

- **`tooling_inventory.md`**: Exhaustive catalog of active runtime CLI tools (`check_execution_readiness.py`, `enforce_runtime_action.py`, etc.).
- **`model_routing.md`**: AI model selection criteria, temperature settings, and routing guidelines.
- **`agent_bootstrap_prompt.txt`**: Canonical system prompt used for initializing repository-aware worker agents.

---

## 3. Core Rules & Invariants

- **Advisory Acceleration**: Repo memory accelerates agent context and maintains task continuity across sessions.
- **Source Code is Ground Truth**: If repo memory conflicts with actual repository source code or ledger state, **source code and ledger remain the sole source of truth**.
- **Atomic Progression**: Whenever a task is approved and committed, the worker or controller must atomically update `project_state.json`, `task_progression.md`, and `task_registry.md` to maintain accurate memory tracking.
