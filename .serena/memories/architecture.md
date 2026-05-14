\# Repository Architecture



utility\_automation\_v2 is a deterministic governance platform.



Core truth model:

\- Ledger is sole source of truth

\- SQLite is projection/cache only

\- Mesh quorum is authority

\- AI is advisory only



System properties:

\- deterministic replay required

\- idempotent execution required

\- fork safety required

\- anti-entropy convergence required



Do not introduce conflicting architectural assumptions.

