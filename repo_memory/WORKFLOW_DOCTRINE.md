# WORKFLOW DOCTRINE
# Updated: 20/05/2569

## Operating Model

```text
GPT / Controller = plan, review, arbitrate, approve
Worker models = inspect, implement, validate, report
Serena = repository truth
Reports = evidence
Repository = durable memory
Chat = decision channel
```

---

## Standard Task Flow

1. Controller issues task or shortcode
2. Worker enters READ-FIRST mode
3. Worker invokes Serena and returns evidence
4. Worker inspects docs/repo/reports
5. Worker returns plan
6. Controller approves checkpoint
7. Worker implements checkpoint only
8. Worker writes reports
9. Worker runs validation
10. Controller reviews
11. Controller approves commit/push

---

## Hard Stops

Worker must stop when:

- scope is ambiguous
- Serena fails for repo-aware work
- working tree is unexpectedly dirty
- code was modified before approval
- schema changes are needed but unapproved
- validation fails repeatedly
- out-of-scope files are touched

---

## Stateless Continuation

A new chat may replace an old chat at any time.

New chat must reconstruct context from:

- repo state
- docs
- repo_memory
- ai_runtime/reports
- Serena evidence
- controller instruction

Do not rely on prior chat history.

---

## Evidence Rule

Claims without evidence are invalid.

Every completion claim must be backed by reports and validation.
