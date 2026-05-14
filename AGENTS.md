# Agent Instructions

## Serena MCP

- Use Serena for all coding work in this repository.
- At the start of a code task, activate this project with Serena and check whether onboarding has been performed.
- Use Serena symbol tools before broad edits: `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`, `find_declaration`, and diagnostics where relevant.
- Prefer Serena edits for symbol-level changes: `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol`, and `rename_symbol`.
- Use normal shell/search tools when Serena is not the right fit, such as repository-wide text search, tests, builds, generated files, Docker commands, and non-code assets.
- Do not use Serena memory as a replacement for repository guidance. Keep durable project rules in tracked files such as this file, `PROJECT_RULES.md`, and `AI_HANDOFF.md`.

## Repository Rules

- Ledger is the only source of truth.
- SQLite is cache/projection only.
- MeshOrchestrator is the only quorum authority.
- AI is advisory only.
- Simulation must never write ledger events.
- Simulation must never call promotion or quorum APIs.
- Never weaken hash, signature, invariant, replay, quorum, audit, or deterministic ordering guarantees.
- Before editing, inspect relevant modules, identify authority boundaries, and keep planned file changes scoped.
- After editing, run targeted tests and report exact validation results.
