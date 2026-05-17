# Architecture Doctrine

## Non-Negotiable Rules

### Ledger Truth
Ledger is sole source of truth.

Never treat:
- SQLite
- dashboard state
- caches
- projections
- inferred state

as authoritative.

Rule:
Ledger > projection > cache > UI

### SQLite
SQLite is projection/cache only.

Never architect authority around SQLite truth.

### AI Advisory Only
AI may advise.
AI may not autonomously govern.

### Determinism
Equivalent inputs must produce equivalent outcomes.

Avoid:
- hidden randomness
- unstable ordering
- transient authority dependencies

### Thin Frontend
Frontend is observability/control surface.

Frontend must not become hidden business authority.

Historical doctrine:
frontend remains GET-only unless explicitly governed otherwise.

### Governance Over Convenience
Shortcuts that weaken auditability are unacceptable.
