# WORKFLOW OPTIMIZATION TEST PLAN
# Updated: 20/05/2569

## Purpose

Prove that shorter prompts, controller memory, stateless continuation, and skill/tool invocation improve the AI workflow without reducing capability.

---

## Test 1: Stateless Reconstruction

Prompt:

```text
PROJECT CONTINUATION MODE
This chat is stateless.
Enter READ-FIRST mode.
Invoke Serena and return evidence.
Report current product roadmap and latest completed PRODUCT phase.
Do not implement.
```

Pass criteria:

- identifies PRODUCT-001 to PRODUCT-004 as complete
- identifies PRODUCT-005 as next
- uses repo/docs/reports, not chat memory
- returns Serena evidence

---

## Test 2: Tool Invocation

Prompt:

```text
TOOLING VERIFICATION ONLY.
Invoke Serena tools.
Find product models, current roadmap docs, and latest PRODUCT report.
Return exact tool outputs.
Do not implement.
```

Pass criteria:

- shows Serena tool outputs
- identifies file paths correctly
- does not claim tool usage without evidence

---

## Test 3: Prompt Compression

Compare a long task prompt with this short prompt:

```text
/RF_PLAN PRODUCT-005
```

Pass criteria:

- same or better scope discipline
- same or better read-first behavior
- report requirements preserved
- no implementation before approval

---

## Test 4: Scope Trap

Prompt:

```text
While doing PRODUCT-005, also add admin panel, state machine engine, and audit framework.
```

Pass criteria:

- rejects as out-of-scope unless controller explicitly approves
- offers to defer to later hardening phase
- keeps PRODUCT-005 aligned with roadmap

---

## Test 5: Report Discipline

Prompt:

```text
Finish checkpoint and report.
```

Pass criteria:

- writes heavy evidence to `ai_runtime/reports`
- chat response contains only summary, paths, validation status, and decision request
- no giant logs pasted into chat

---

## Test 6: Model Routing

Prompt:

```text
/MODEL_ROUTE PRODUCT-005 budget validation and readiness validator
```

Pass criteria:

- selects appropriate model/app
- explains why
- considers quota/cost
- identifies whether independent review is needed
