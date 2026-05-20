# CONTROLLER MEMORY
# Updated: 20/05/2569

## Purpose

This is the controller operating memory for `utility_automation_v2_light`.

It is intended to reduce long prompts and allow stateless chat continuation.

---

## Project Mission

Build a municipal utility disbursement assistant for Thai local-government workflow.

Core workflow:

```text
สร้างงานเบิกจ่ายใหม่
→ อัปโหลดบิล PDF / เอกสาร
→ OCR / extraction
→ ผู้ใช้ตรวจ/แก้
→ ตรวจยอด / VAT / ความครบถ้วน
→ จัดทำข้อมูลฎีกา
→ สร้างบันทึกข้อความ Word
→ เตรียมข้อมูล e-LAAS
→ ปิดงาน
```

---

## Current Product Status

Completed:

- PRODUCT-001: Main dashboard and product baseline
- PRODUCT-002: Case document intake and registry
- PRODUCT-003: OCR / extraction integration
- PRODUCT-004: Word memo generation

Next planned:

- PRODUCT-005: Budget integration + submission readiness validator
- PRODUCT-006: Data quality guardrails
- PRODUCT-007: e-LAAS assist
- PRODUCT-008: optional browser assist
- PRODUCT-009: polish / acceptance

---

## Approved Enhancements

The following additions are approved because they improve real workflow without overengineering:

1. Submission Readiness Validator
2. Provider Alias Mapping
3. Duplicate Bill Guard

---

## Controller Role

The controller may:

- define roadmap
- approve scope changes
- request independent model review
- require reports and validation
- approve/reject commits
- escalate to stronger models/tools

The controller should not rely on chat history alone.

---

## AI Role Split

- ChatGPT / GPT-5.5: controller, planner, reviewer, doctrine, scope guard
- Codex / GPT-5.5: independent code review and repo verification
- Gemini CLI / Gemini 3.1 Pro: heavy repo implementation
- Gemini 3.5 Flash: fast checkpoint worker
- Sonnet / Opus 4.6 Thinking: tricky backend, Word/docx, careful refactor
- OpenCode / Gemma 4 / free models: experiments and cheap iteration
- Serena: repository reality anchor

---

## Operating Doctrine

- READ-FIRST is mandatory
- Serena evidence is mandatory for repo-aware work
- reports go to `ai_runtime/reports`
- chat is controller channel only
- heavy evidence belongs in files
- no implementation before approval unless explicitly authorized
- no commit/push without approval
- follow roadmap unless there is a valid blocker or approved deviation

---

## Known Constraints

- Windows environment
- mixed CRLF/LF warnings are common and usually not blockers
- Tesseract binary may be required for real OCR runtime
- `data/uploads/` and `data/generated/` must not be committed
- older governance docs may conflict with product mutations; distinguish governance console vs product app
