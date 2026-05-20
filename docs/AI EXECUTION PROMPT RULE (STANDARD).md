#20/05/2569 17.52

# AI EXECUTION PROMPT RULE (STANDARD)

Append this section to every implementation work order.

---

## Mandatory Execution Discipline

### READ-FIRST (MANDATORY)

Before any implementation:

- Enter READ-FIRST mode.
- Activate all relevant project skills.
- Use all relevant repository/project tooling automatically (e.g. Serena, repo inspection tooling, project memory, architecture maps).
- Inspect the actual current repository state before editing.
- Identify reusable extension points before creating new code.
- Do NOT implement from memory.
- Do NOT assume architecture.

Minimum inspection:

- git status
- git log --oneline -5
- relevant src/product/*
- relevant frontend/product-ui/*
- relevant tests/*
- current architecture / handoff docs if applicable

Required pre-implementation output:

1. architecture summary
2. reusable components
3. extension points
4. schema gaps / blockers
5. implementation plan

DO NOT IMPLEMENT until approval.

---

## Implementation Constraints

During implementation:

- Keep changes inside approved scope only.
- Do NOT modify legacy/governance/control-plane code unless explicitly approved.
- Prefer extension over rewrite.
- If architectural blockers are discovered:
  STOP
  REPORT
  REQUEST APPROVAL

Do NOT silently change roadmap.

Allowed roadmap change reasons:

- architecture blocker
- dependency inversion
- risk reduction
- schema gap
- integration impossibility

Not valid reasons:

- "thought this would be better"
- "user casually asked"
- "felt cleaner"

---

## Validation & Reporting (MANDATORY)

After implementation:

Write execution artifacts to:

D:\utility_automation_v2_light\ai_runtime\reports

Required files:

- PRODUCT-XXX-worker-report.md
- PRODUCT-XXX-validation-output.txt
- PRODUCT-XXX-runtime-manifest.json

Recommended files:

- PRODUCT-XXX-execution-transcript.md
- PRODUCT-XXX-tool-trace.json
- PRODUCT-XXX-walkthrough.md

---

## Report Content Requirements

Reports must contain:

### Worker Report

- exact files created
- exact files modified
- architecture decisions
- reuse decisions
- deferred risks
- scope confirmation

### Validation Output

Exact raw outputs of:

- pytest
- npm build
- lint
- runtime smoke tests
- API verification
- upload verification
- integration verification

### Runtime Manifest

Structured machine-readable summary:

- task id
- branch
- commit (if approved)
- changed files
- validation commands
- timestamps
- generated artifacts
- hashes if relevant

---

## Git Hygiene

Before commit:

Run:

git diff --cached --check

Verify no staging of:

- __pycache__
- .next
- node_modules
- *.db
- uploads
- temporary artifacts
- videos
- mockup references
- archives

Stage ONLY approved files.

Do NOT commit without controller approval.
Do NOT push without controller approval.

---

## Final Response Format

Return:

1. exact changed files
2. validation evidence
3. git hygiene summary
4. known risks
5. approval request

Never claim completion without evidence.