# TASK COMMAND SHORTCODES
# Updated: 20/05/2569

## Purpose

Use short controller commands instead of long repeated prompts.

Workers must resolve each shortcode by reading docs, repo memory, reports, skills, and Serena evidence.

---

## General Rule

A shortcode does not remove governance requirements.

Every implementation-related shortcode still requires:

- READ-FIRST mode
- explicit Serena evidence
- repository inspection
- report artifacts
- validation output
- controller approval gates

---

## Shortcodes

### `/RF_PLAN PRODUCT-XXX`

Read-first planning only.

Required behavior:

- inspect `docs/`
- inspect `repo_memory/`
- inspect latest `ai_runtime/reports/`
- invoke Serena and return tool outputs
- inspect relevant source files
- return plan
- do not modify code

---

### `/EXEC_CP1 PRODUCT-XXX`

Execute checkpoint 1 only.

Required behavior:

- confirm approved plan
- implement only checkpoint 1 scope
- stop after checkpoint completion
- write reports
- do not commit
- do not push

---

### `/REVIEW_CLOSE PRODUCT-XXX`

Prepare final review package before commit.

Required evidence:

- exact changed files
- `git status --short`
- `git diff --stat`
- `git diff --cached --check` if staged
- validation output
- report paths
- known risks

---

### `/RECOVERY_REVIEW`

Use when an agent modified code before approval or scope drift is suspected.

Required behavior:

- stop all edits immediately
- do not commit
- do not push
- report exact modified files
- report architectural assumptions
- report validation status
- wait for controller decision

---

### `/MODEL_ROUTE <task description>`

Return recommended app/model and reason.

Must consider:

- task difficulty
- quota status
- cost
- model strengths
- current tool availability
- whether independent review is needed

---

### `/REPORT_ONLY PRODUCT-XXX`

Write or update report artifacts only.

No source-code modifications allowed.
