# SOURCE OF TRUTH
# Updated: 20/05/2569

## Purpose

This document defines the priority order for project truth when instructions, docs, reports, chat history, or AI memory disagree.

The goal is to keep AI workers aligned with the current product plan while still preserving governance discipline.

---

## Canonical Priority Order

When sources conflict, use this order:

1. **Latest explicit controller instruction**
2. **Current repository state**
3. **`repo_memory/` controller memory and roadmap**
4. **`docs/` project doctrine and operating rules**
5. **`ai_runtime/reports/` execution evidence**
6. **Central AI Tools Kit skills** from `D:\ai-tools\ai-tools-kit`
7. **App-local skill copies**
8. **External references** such as Agentpedia, OpenAI, Gemini CLI, Antigravity docs
9. **Chat history** only as advisory context, never as source of truth

---

## Repository Reality Rule

If chat memory conflicts with current source files, inspect the repository and prefer repository reality.

Required evidence for repository claims:

- `git status`
- relevant file inspection
- Serena tool output when available
- test/build output when claiming functionality

---

## Controller Override Rule

The controller may intentionally override a prior document, roadmap, or report.

Valid override reasons:

- blocker
- schema gap
- dependency inversion
- risk reduction
- mission correction
- explicit roadmap adjustment

The AI worker must surface the conflict and follow the latest controller decision.

---

## Product vs Governance Scope Note

Older governance rules may say dashboard/operator surfaces are read-only and forbid POST/PUT/PATCH/DELETE.

That rule applies to the **legacy governance/runtime console**.

It does **not** prohibit approved product application flows such as:

- `POST /api/cases`
- `POST /api/cases/{case_id}/documents`
- `POST /api/cases/{case_id}/memo/generate`


---

## Product Execution Override Rule

For current product execution:

PRODUCT roadmap and controller instructions override legacy TASK registries unless those legacy task systems are explicitly reactivated by controller instruction.

Examples:

Current:
- PRODUCT-001
- PRODUCT-002
- PRODUCT-003
- PRODUCT-004
- PRODUCT-005

Legacy references such as TASK-088 / TASK-101 are historical execution artifacts unless explicitly reactivated.

