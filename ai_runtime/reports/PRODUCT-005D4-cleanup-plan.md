# PRODUCT-005D4 — Workspace Cleanup Plan

## 1. Overview
Following the closure of PRODUCT-005, the workspace contains numerous untracked artifacts. This plan classifies these files to ensure a clean transition to PRODUCT-006 without risking the loss of critical evidence or contaminating the repository with temporary artifacts.

## 2. Untracked File Classification

### Group A: Tooling & Metadata (Keep but do not commit)
*Files required for current AI agent operations and local indexing.*
- `.antigravitycli/`
- `.codegraph/`
- `.codex/`
- `.mcp.json` (if untracked)
- `opencode.json` (if untracked)
- `ALL_CONTEXT_BUNDLE.md` (Local context assembly)

**Recommended Action**: Maintain locally. Add to `.gitignore` to stop tracking warnings.

### Group B: Evidence & Reports (Commit later / Move to archive)
*Reports and evidence generated during PRODUCT-005. Should be preserved for audit.*
- `ai_runtime/reports/` (All `PRODUCT-005*` reports and manifests)
- `ai_runtime/contracts/`
- `ai_runtime/inbox/`
- `B_RemainedBudget.xlsx` (Source evidence)
- `frontend_file_inventory.*`
- `ui_file_inventory.*`
- `markdown_command_workflow_hits.csv`
- `markdown_files_to_review.txt`

**Recommended Action**: Move to a designated `archive/PRODUCT-005/` directory outside the root or commit to a dedicated evidence branch if required by governance.

### Group C: Backup & Archives (Backup outside repo)
*Large compressed files and backups that bloat the workspace.*
- `Root.zip`
- `ai_runtime.zip`
- `utility_automation_v2_light.rar`
- `utility_automation_v2_light.zip`
- `utility_automation_v2_light/` (Nested folder copy)
- `[Thai_named_dir]/` (Possible backup/temp folder)

**Recommended Action**: Move to an external backup drive/cloud storage. **Delete from workspace after backup.**

### Group D: Temporary / Junk (Delete)
*Drafts, screenshots, and transient files.*
- `Elaas.mp4` (Video recording)
- `mocup.html`
- `mocup.jpg`
- `README_APPLY.md` (Likely a draft)
- `docs/New Text Document.txt`

**Recommended Action**: Delete.

### Group E: Project-Specific (Commit later)
*High-level planning documents that may be needed for the next milestone.*
- `1. PRODUCT MISSION RECOVERY PLAN.md`

**Recommended Action**: Review and commit to `docs/` or `repo_memory/` if they are now finalized.

---

## 3. Proposed .gitignore Additions
To prevent these from reappearing as "untracked" in future checks:
```gitignore
# AI Tooling
.antigravitycli/
.codegraph/
.codex/

# Local Evidence/Artifacts
B_RemainedBudget.xlsx
*.zip
*.rar
*.mp4
*.html
*.jpg
ai_runtime/
ALL_CONTEXT_BUNDLE.md
*_inventory.*
*_workflow_hits.*
*_files_to_review.*
```

## 4. Safe Cleanup Sequence
1. **Backup**: Move all Group C files to external storage.
2. **Archive**: Move Group B to an external evidence store.
3. **Prune**: Delete Group D files.
4. **Finalize**: Add Group A and B patterns to `.gitignore`.
5. **Promote**: Move Group E to tracked documentation.

## 5. Risk Analysis
| Group | Risk if Deleted | Mitigation |
| :--- | :--- | :--- |
| Group A | Loss of AI context/index (must re-index) | Keep locally; ignore in git. |
| Group B | Loss of audit trail for PRODUCT-005 | Backup to `ai_runtime/` archive before deletion. |
| Group C | Loss of previous state backups | Verify integrity of external backup. |
| Group D | Negligible | None required. |

## 6. Final Status & Confirmation
- **Current Git Status**: Working tree is clean of tracked changes.
- **Confirmation**: 
  - No files deleted, moved, or edited during this planning phase.
  - No files staged, committed, or pushed.
