---
name: review-gate-governance
description: Pre-commit controller review gate for scope, determinism, validation, and authority safety.
---

# Review Gate Governance

## PASS Criteria

PASS only if:

- scope respected
- no speculative refactor
- no fabricated validation
- no fake inspection
- deterministic invariants preserved
- no forbidden authority surfaces
- tests actually run
- exact git diff reviewed
- exact validation output provided

## Frontend Rule

Frontend remains GET-only except explicitly approved bounded runtime operator actions.

Any POST/PUT/PATCH/DELETE requires:

- exact task approval
- exact route allowlist
- typed payload schemas
- fail-closed validation
- no hidden authority expansion

## High-Risk Red Flags

FAIL if:

- certifier weakened broadly
- broad allowlists added
- fake defaults introduced
- any payload typed as any when exact types exist
- arbitrary shell/subprocess bridge added
- direct artifact/contract/ledger mutation added outside approved tooling
- commit/push performed before approval

## Output

Return:

PASS or FAIL

If FAIL:

- exact reason
- exact file/path
- exact remediation
