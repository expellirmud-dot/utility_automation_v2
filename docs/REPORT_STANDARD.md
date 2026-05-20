# REPORT STANDARD
# Updated: 20/05/2569

## Purpose

This document defines how AI workers must report implementation, validation, and review evidence.

The chat must stay light. Heavy evidence belongs in files.

---

## Report Location

All execution evidence must be written to:

```text
D:\utility_automation_v2_light\ai_runtime\reports
```

---

## Required Report Artifacts

For each PRODUCT task or checkpoint, create at minimum:

```text
PRODUCT-XXX-worker-report.md
PRODUCT-XXX-validation-output.txt
PRODUCT-XXX-runtime-manifest.json
```

Recommended when useful:

```text
PRODUCT-XXX-read-first-report.md
PRODUCT-XXX-execution-transcript.md
PRODUCT-XXX-tool-trace.json
PRODUCT-XXX-walkthrough.md
```

---

## Worker Report Must Include

- task id and checkpoint id
- exact files created
- exact files modified
- exact files deleted, if any
- architecture decisions
- reuse decisions
- scope confirmation
- known risks
- deferred items
- confirmation that no out-of-scope files were modified

---

## Validation Output Must Include

Raw command outputs or exact summaries for:

- `python -m pytest tests/product -q`
- `npm run build` for `frontend/product-ui` when frontend changed
- targeted tests relevant to the task
- artifact proof such as generated file path, file size, existence check
- `git diff --cached --check` before commit

---

## Runtime Manifest Must Include

Machine-readable metadata:

- task id
- branch
- commit id if approved
- changed files
- validation commands
- generated report paths
- generated artifact paths
- known risks
- timestamps

---

## Chat Report Format

In chat, workers should not paste huge logs.

The chat response should contain only:

1. short summary
2. exact changed files
3. validation status
4. report file paths
5. known risks
6. decision requested

---

## Forbidden Chat Payloads

Do not paste these into the controller chat unless explicitly requested:

- full git diff
- full pytest log
- full npm build log
- full source code dumps
- large markdown bundles
- giant tables
- raw generated documents

Write them into `ai_runtime/reports` instead.
