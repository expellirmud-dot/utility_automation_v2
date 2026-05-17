# AI Runtime Handoff Loop

Purpose:
Reduce manual relay between ChatGPT (controller) and Gemini CLI (worker),
while preserving human approval and project governance.

Flow:
1. Controller creates task in inbox
2. Gemini reads task
3. Gemini writes report
4. ChatGPT reviews report
5. Human approves
6. Gemini implements approved scope
7. Validation report
8. Archive

State model:
DRAFT
READ_FIRST
WAITING_GPT_REVIEW
APPROVED_FOR_IMPLEMENTATION
IMPLEMENTED
VALIDATED
BLOCKED
ARCHIVED

Rules:
- READ-FIRST mandatory
- Serena when relevant
- no implementation from memory
- no fake validation
- human approval required
- project-local governance overrides defaults
