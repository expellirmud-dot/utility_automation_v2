# Audit Review Prompt

Read first:
- PROJECT_RULES.md
- AI_HANDOFF.md
- AGENTS.md

Review the current changes only.

Check for:
- invariant violations
- authority escalation
- mutation APIs
- forbidden imports
- nondeterministic behavior
- hidden framework migration
- unrelated rewrites
- dependency churn

For ops/dashboard changes verify:
- GET-only APIs
- read-only UI
- no action controls
- no POST/PUT/PATCH/DELETE
- no control-plane coupling

Do not modify files unless explicitly instructed.

Report:
- pass/fail summary
- concrete risks
- exact files involved
- recommended minimal fixes
