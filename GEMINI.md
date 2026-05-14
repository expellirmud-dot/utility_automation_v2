# GEMINI.md

## Operating Mode

You are working inside utility_automation_v2.

Read before work:
- PROJECT_RULES.md
- AI_HANDOFF.md
- AGENTS.md

## Gemini-Specific Guidance

Use Gemini for:
- long-context implementation work
- multi-file stitching
- boilerplate generation
- dashboard plumbing
- repetitive test scaffolding

Do:
- stay inside assigned scope
- preserve architecture
- prefer minimal localized diffs
- preserve deterministic guarantees
- preserve tests

Do not:
- invent architecture authority
- expand scope implicitly
- introduce dependency churn
- perform repo-wide rewrites
- migrate frameworks unless task explicitly authorizes it

Completion:
- run required validation
- report exact command outputs
