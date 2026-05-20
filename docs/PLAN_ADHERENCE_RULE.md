# PLAN ADHERENCE RULE
# Updated: 20/05/2569

## Purpose

Keep the project aligned with the approved mission plan and prevent accidental scope expansion.

---

## Primary Rule

Follow the roadmap by default.

Do not add phases, frameworks, architecture layers, or cleanup work simply because they seem useful.

---

## Valid Reasons to Change the Plan

A roadmap change may be proposed only for:

- real blocker
- schema gap
- dependency inversion
- risk reduction
- implementation impossibility
- explicit controller approval

---

## Invalid Reasons

Do not change the roadmap because:

- the AI thinks it is cleaner
- the worker wants to refactor
- the user casually asks a question
- a generic best practice suggests extra architecture
- legacy governance platform patterns are available

---

## Recovery Rule

If a task must temporarily deviate:

1. state why
2. state the minimum deviation
3. request approval
4. implement only the approved deviation
5. return to the roadmap immediately

---

## Approved Mission Enhancements

The following are approved because impact is high and complexity is low:

1. Submission Readiness Validator
2. Provider Alias Mapping
3. Duplicate Bill Guard

These are part of the product roadmap, not scope creep.
