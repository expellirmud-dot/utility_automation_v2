# Bootstrap Prompts

## ChatGPT New Session Bootstrap

Use this when starting a new ChatGPT session:

```text
Continuation session.

Before making recommendations about this project, architecture, AI workflow, Gemini, Serena, governance, or implementation approach:

Read:
D:\utility_automation_v2\ai_context\AI_OPERATING_CONTEXT.md

Follow linked context documents as needed.

Treat ai_context as institutional memory and source of truth.
Preserve continuity.
Do not redesign established workflow unless explicitly instructed.
Distinguish facts from unknowns.
Inspect repository reality when needed.
Gemini CLI Project Bootstrap

Use this inside Gemini CLI from project root:

Run READ-FIRST workflow.
Use project-local instructions first.
Use Serena when relevant.
Do not edit files.
Return inspection report only.
Deep Architecture Audit Prompt
Run READ-FIRST workflow.
Use Serena.
Perform source-backed architecture audit.
Do not rely only on documentation.
Inspect actual source modules.
Do not implement anything.
Separate evidence from assumptions.
Safe Implementation Prompt
Run READ-FIRST workflow.
Use Serena.
Inspect actual files first.
State root cause and exact files to change.
Do not edit until scope is explicit.
After edits, run exact validation and report outputs.

