# Architecture Map

## Core Truth Model

- Ledger is the sole source of truth
- SQLite is projection/cache only
- Mesh quorum is sole runtime authority
- AI is advisory only

## Governance Properties

- deterministic replay
- canonical ordering
- certification reproducibility
- auditability
- fail-closed governance

## Governance Chain

Certification
-> Promotion Gatekeeper
-> Promotion Governance
-> Release Authorization Advisory

## Forbidden Authority Actions

- ledger mutation
- mesh quorum execution
- runtime promotion execution
- recovery execution
- policy promotion by AI
- frontend mutation authority
