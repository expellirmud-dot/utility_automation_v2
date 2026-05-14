\# GEMINI.md



\## Operating Mode



You are working inside a deterministic governance platform.



This repository has strict invariants.



Mandatory rules:

\- read PROJECT\_RULES.md

\- read AI\_HANDOFF.md

\- obey AGENTS.md

\- stay inside assigned scope only



\---



\## Architecture Rules



Never assume authority.



Truth model:

\- Ledger = sole source of truth

\- SQLite = read-only projection/cache

\- Mesh quorum = authority

\- AI = advisory only



Never violate determinism.



\---



\## Task Execution Rules



Preferred:

\- minimal diffs

\- localized implementation

\- preserve existing architecture

\- additive changes

\- targeted tests



Forbidden:

\- architecture expansion

\- framework migration

\- speculative refactors

\- repo-wide rewrites

\- dependency churn



\---



\## Dashboard Rules



Ops dashboard is read-only.



Allowed:

\- GET-only data display

\- UI improvements

\- projection visualization



Forbidden:

\- mutation APIs

\- action controls

\- replay triggers

\- recovery execution

\- policy authority actions



\---



\## Completion Rules



Before completion:

\- run pytest

\- if runtime/governance changed, run deterministic certifier

\- report exact outputs

