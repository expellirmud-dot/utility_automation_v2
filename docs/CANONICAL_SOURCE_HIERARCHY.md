# Canonical Source Hierarchy

To maintain absolute determinism and resolve conflicts between specifications, documentation, and source code, the `utility_automation_v2` platform enforces a rigorous 5-tier canonical source hierarchy.

```
+-----------------------------------------------------------------------+
| 1. ROOT GOVERNANCE LAYER (Absolute Authority)                         |
|    AGENTS.md | GEMINI.md | PROJECT_RULES.md | AI_HANDOFF.md           |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| 2. GOVERNED RUNTIME LAYER (Cryptographic & Physical Gate Authority)   |
|    ai_runtime/governance/RUNTIME_WORKFLOW.md | ai_runtime/contracts/  |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| 3. CONSOLIDATED OPERATIONAL DOCS LAYER (Onboarding & Roles)           |
|    docs/CURRENT_RUNTIME_WORKFLOW.md | QUICKSTART.md | AGENT_ROLE_MAP.md|
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| 4. PERSISTENT REPOSITORY MEMORY LAYER (Advisory Synchronization)      |
|    repo_memory/project_state.json | task_registry.md | ...            |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
| 5. HISTORICAL AI CONTEXT LAYER (Legacy Reference & Background ADRs)   |
|    ai_context/1.2 AI_CONTEXT_MASTER.md | DECISION_HISTORY.md | ...    |
+-----------------------------------------------------------------------+
```

---

## 1. Hierarchy Rules & Conflict Resolution

### Tier 1: Root Governance Layer
- **Files**: `AGENTS.md`, `GEMINI.md`, `PROJECT_RULES.md`, `AI_HANDOFF.md`.
- **Authority**: Non-negotiable repository invariants. In the event of any conflict, Tier 1 overrides all subsequent tiers.

### Tier 2: Governed Runtime Layer
- **Files**: `ai_runtime/governance/RUNTIME_WORKFLOW.md`, active execution contracts (`ai_runtime/contracts/*.json`), and verification tools (`src/tools/runtime/`).
- **Authority**: Physical CLI enforcement. No agent or operator can execute actions or validate evidence that violates active Tier 2 contract boundaries.

### Tier 3: Consolidated Operational Documentation Layer
- **Files**: `docs/CURRENT_RUNTIME_WORKFLOW.md`, `docs/QUICKSTART.md`, `docs/AGENT_ROLE_MAP.md`, `docs/ANTI_PATTERNS.md`.
- **Authority**: Authoritative human and agent onboarding guidelines and role boundaries.

### Tier 4: Persistent Repository Memory Layer
- **Files**: `repo_memory/project_state.json`, `task_registry.md`, `task_progression.md`, `architecture_map.md`.
- **Authority**: Advisory synchronization layer. Accelerates context loading but is subordinate to physical repository source code and ledger truth.

### Tier 5: Historical AI Context Layer
- **Files**: `ai_context/*`.
- **Authority**: Background institutional memory and legacy architectural decision records. Subordinate to Tier 3 and Tier 4 in current operational workflows.
