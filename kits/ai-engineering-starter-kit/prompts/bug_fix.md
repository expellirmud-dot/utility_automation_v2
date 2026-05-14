# Bug Fix Prompt

Read first:
- PROJECT_RULES.md
- AI_HANDOFF.md
- AGENTS.md

Fix only the reported bug.

Rules:
- do not weaken tests
- do not skip tests
- do not change certifier logic
- do not broaden scope
- do not mask the failure
- preserve deterministic behavior

Process:
1. reproduce the failure
2. identify root cause
3. make minimal fix
4. run targeted test
5. run full test suite if relevant
6. report exact results

Prefer:
- deterministic ordering
- explicit state handling
- stable tie-breaking
- local fixes

Report:
- root cause
- fix summary
- files changed
- validation commands
- exact outputs
