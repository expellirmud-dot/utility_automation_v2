# RUNTIME OPERATOR WORKFLOW

## Purpose
This workflow defines governed browser-based runtime task execution for the operator console.

Goals:
- governed runtime task execution
- bounded human-triggered actions
- browser operator control
- deterministic operational workflow

Non-goals:
- autonomous authority mutation
- self-approval
- direct ledger mutation
- hidden execution channels

---

## Core Principles

- Human initiated only
- READ-FIRST mandatory
- Inspect payload before execution
- Delegate only to governed runtime tooling
- No direct ledger mutation
- No direct contract mutation
- No direct mesh/quorum mutation
- No autonomous approval
- Fail closed on invalid requests

---

## Standard Task Lifecycle

### 1. Create Task
Create a controller execution request.

Required inputs:
- Task ID
- Title
- Objective
- Architectural rationale
- Scope
- Candidate modules
- Tests
- Validation commands
- Acceptance criteria
- Constraints

Rule:

> Do not create incomplete controller requests.

---

### 2. Inspect Payload (MANDATORY)
Inspect the execution payload before starting.

Verify:
- task id
- repo path
- branch
- constraints
- validation commands
- governance boundaries
- runtime artifact targets
- expected outputs

Rule:

> Never start execution without payload inspection.

---

### 3. Start Task
Start governed execution.

Expected behavior:
- controller request validation
- execution contract issuance
- readiness verification

Expected outputs:
- contract id
- runtime task state
- worker assignment

Rule:

> Failed validation must abort execution.

---

### 4. Monitor Execution
Operator monitors execution.

Check for:
- READ-FIRST compliance
- actual file inspection
- scoped implementation only
- validation progress
- no unauthorized mutation
- governance boundary compliance

Red flags:
- implementation from memory
- fake defaults
- certification weakening
- broad allowlists
- arbitrary command execution

---

### 5. Review Implementation
Before finishing:

Required review:
- git diff review
- governance review
- validation evidence review
- changed files review

Rule:

> Do not finish blindly.

---

### 6. Finish Task
Finalize task execution.

Expected behavior:
- runtime artifact validation
- evidence generation
- completion lifecycle update

Expected outputs:
- completion evidence
- worker report
- validation output

---

### 7. Post-Completion Continuity
Required continuity updates:
- AI_HANDOFF.md
- repo_memory/project_state.json
- repo_memory/task_registry.md
- repo_memory/task_progression.md

Commit pattern:

1. implementation commit
2. continuity commit

---

## UI Action Mapping

| UI Action | Meaning |
|---------|---------|
| Create Task | Create controller execution request |
| Inspect Payload | Inspect exact execution payload |
| Start Task | Validate request + issue contract + begin execution |
| Finish Task | Validate artifacts + finalize lifecycle |
| Inspect Task | Inspect runtime task state |

---

## Forbidden Actions

Never allow:
- direct ledger mutation
- direct contract mutation
- direct mesh mutation
- direct quorum mutation
- autonomous commit
- autonomous push
- self approval
- hidden execution channels
- arbitrary shell execution

---

## Troubleshooting

### Backend Offline
Symptom:

`ECONNREFUSED 127.0.0.1:8000`

Fix:

```powershell
$env:PYTHONPATH="."
python -m uvicorn src.ui.ops_overview_api:app --host 127.0.0.1 --port 8000 --reload
```

---

### Frontend Running But No Data
Check:
- backend server running
- API route reachable
- correct localhost port
2) Frontend (Next.js)

cd D:\utility_automation_v2_light\frontend\operator-observatory
npm run dev
จะได้:
http://localhost:3000
---

### Task Stuck In Execution
Check:
- validation step running
- shell awaiting input
- worker waiting for controller review

---

## Recommended Operational Flow

Create Task
→ Inspect Payload
→ Start Task
→ Monitor Execution
→ Review Diff
→ Review Validation
→ Finish Task
→ Continuity Update

