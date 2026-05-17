---
name: review-gate-governance
description: Review implementation for scope, determinism, validation, and authority safety.
---

CHECK:
- scope respected
- no speculative refactor
- no fabricated validation
- no fake inspection
- deterministic invariants preserved
- no forbidden authority surfaces
- frontend remains GET-only if touched
- tests actually run

OUTPUT:
PASS or FAIL

If FAIL:
- exact reason
- exact remediation
