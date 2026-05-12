```
TASK 039-S1 Architecture Overview
==================================

Deterministic Recovery Proposal Engine Foundation
(No execution, no mesh integration, no ledger mutation)


                           ┌─────────────────────────────────────────┐
                           │   Recovery Signal Detection             │
                           │   (health checks, divergence, crashes)   │
                           └──────────────┬──────────────────────────┘
                                          │
                                          ▼
                           ┌─────────────────────────────────────────┐
                           │   RecoverySignal (Frozen)               │
                           │  - source, signal_type, severity        │
                           │  - epoch, seq_id                        │
                           │  - evidence_hashes (sorted)             │
                           │  - metadata (normalized)                │
                           └──────────────┬──────────────────────────┘
                                          │
                                          ▼
                           ┌─────────────────────────────────────────┐
                           │   Recovery Diagnosis (Frozen)           │
                           │  - classification (isolated/systemic)   │
                           │  - identified_failures (sorted)         │
                           │  - root_cause_hypothesis                │
                           │  - confidence [0.0-1.0]                 │
                           │  - evidence_count                       │
                           └──────────────┬──────────────────────────┘
                                          │
                                          ▼
         ┌──────────────────────────────────────────────────────────┐
         │                  Recovery Plan (Frozen)                  │
         │  ┌────────────────────────────────────────────────────┐ │
         │  │ RecoveryStep (ordered by precedence):             │ │
         │  │  1. ISOLATE_WORKER                               │ │
         │  │  2. RUN_REPLAY_VERIFICATION                      │ │
         │  │  3. REBUILD_SQLITE_PROJECTION                    │ │
         │  │  4. REQUEST_QUORUM_REPAIR                        │ │
         │  │  5. ROLLBACK_TO_LEDGER_POINT                     │ │
         │  │  6. RESTART_NODE                                 │ │
         │  │                                                   │ │
         │  │ Each step: target, reason, parameters            │ │
         │  └────────────────────────────────────────────────────┘ │
         └──────────────┬──────────────────────────────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────────────────────────────┐
     │            Recovery Proposal (Frozen)                        │
     │  ┌────────────────────────────────────────────────────────┐ │
     │  │ signal + diagnosis + plan                             │ │
     │  │ signal.epoch + signal.seq_id identify source order    │ │
     │  │ reason_for_proposal                                   │ │
     │  │                                                        │ │
     │  │ proposal_hash = SHA256(canonical JSON)                │ │
     │  │   (signal_hash + diagnosis_hash + plan_hash +         │ │
     │  │    reason only; no timestamp)                         │ │
     │  │                                                        │ │
     │  │ ⚠️ AI ADVICE NEVER INCLUDED IN HASH                   │ │
     │  └────────────────────────────────────────────────────────┘ │
     └──────────────┬──────────────────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌─────────────────┐   ┌──────────────────────┐
    │ RecoveryReport  │   │ RecoveryAIAdvice     │
    │  (Frozen)       │   │ (Separate object)    │
    │ - proposal      │   │ - confidence_adj     │
    │ - report_hash   │   │ - alternatives       │
    │                 │   │ - warnings           │
    │ report_hash =   │   │ - notes              │
    │  SHA256(        │   │ - model_used         │
    │  proposal_hash) │   │                      │
    │                 │   │ 🚫 NOT IN HASHES     │
    └─────────────────┘   └──────────────────────┘


SAFETY GATE (AST Analysis)
==========================

  Forbidden symbols → BLOCKED:
  ├─ Ledger: append_event, commit_event, write_ledger
  ├─ Policy: promote, promote_policy, promote_stage
  ├─ Mesh: submit_critical_event, submit_recovery_proposal
  ├─ SQLite: execute, insert, update, delete
  └─ Classes: MeshOrchestrator, QuorumAuthority

  Allowed operations → PASS:
  ├─ detect, analyze, classify, normalize
  ├─ hash, compute_hash, stable_hash
  ├─ build, create, construct, plan
  └─ verify, validate, check

  Result: FAIL-CLOSED (safety violation = exception)


DETERMINISTIC HASHING
======================

  Canonical JSON generation:
  ├─ Sort all dict keys (recursive)
  ├─ Sort all sequences (tuples/lists)
  ├─ No timestamps in proposal identity
  ├─ No Python repr
  └─ No enum implicit ordering

  Hash computation:
  (PROPOSAL) = SHA256(JSON(
    signal_hash +
    diagnosis_hash +
    plan_hash +
    reason_for_proposal
  ))

  Hash verification:
  ├─ verify_proposal_hash(proposal, expected) → bool
  ├─ verify_report_hash(report, expected) → bool
  └─ All deterministic (same input = same hash always)


RECOVERY STEP PRECEDENCE
=========================

  Proposal precedence ordering (deterministic proposal ordering):

  Index  Type                           Target          Reason
  ─────  ─────────────────────────────  ──────────────  ──────────────
    1    ISOLATE_WORKER                 worker          Prevent cascade
                                                        failure
    2    RUN_REPLAY_VERIFICATION        ledger          Verify ledger
                                                        integrity post-
                                                        isolation
    3    REBUILD_SQLITE_PROJECTION      sqlite_cache    Rebuild cache
                                                        from ledger
    4    REQUEST_QUORUM_REPAIR          quorum          Ask mesh to heal
                                                        any splits
    5    ROLLBACK_TO_LEDGER_POINT       system          Rollback to
                                                        known good
                                                        point
    6    RESTART_NODE                   node            Restart after
                                                        cleanup


INVARIANTS
==========

  ✅ Ledger = Truth
     └─ No ledger writes from recovery subsystem

  ✅ Deterministic Hashing
     └─ Same input → same hash (always)
     └─ Different input → different hash
     └─ AI advice excluded from all hashes

  ✅ Frozen Models
     └─ All @dataclass(frozen=True)
     └─ Immutable after construction
     └─ Safe for concurrent access

  ✅ Canonical Ordering
     └─ Evidence hashes sorted
     └─ Failures sorted
     └─ Steps sorted by precedence
     └─ Dicts sorted by keys

  ✅ Fail-Closed Safety
     └─ AST detects forbidden symbols
     └─ Safety violations raise exceptions
     └─ No silent failures

  ✅ AI Advice Segregation
     └─ Separate object (RecoveryAIAdvice)
     └─ Never in deterministic hashes
     └─ Serializable for logging/display


CONSTRAINTS (S1)
================

  ✅ ALLOWED (S1 scope):
     ├─ Detect recovery signals
     ├─ Normalize inputs deterministically
     ├─ Classify failures
     ├─ Plan recovery steps
     ├─ Build proposal objects (immutable)
     ├─ Compute deterministic hashes
     ├─ Provide AST safety gates
     └─ Serialize reports for display

  ❌ NOT ALLOWED (S2+):
     ├─ Carry out approved recovery actions
     ├─ Integrate MeshOrchestrator (→S2)
     ├─ Submit proposals to mesh (→S2)
     ├─ Call quorum APIs (→S2+)
     ├─ Mutate ledger/SQLite
     ├─ Promote policies
     ├─ Implement self-healing
     └─ Include AI in deterministic hashes


DEPLOYMENT & TESTING
=====================

  Test coverage: 34/34 passing
  ├─ Frozen immutability: 7 tests
  ├─ Deterministic hashing: 3 tests
  ├─ AI advice exclusion: 2 tests
  ├─ Canonical ordering: 4 tests
  ├─ Signal normalization: 2 tests
  ├─ Safety gate: 9 tests
  ├─ Fail-closed behavior: 3 tests
  ├─ Canonical JSON: 2 tests
  └─ Non-regression: 2 tests

  Non-regression verification:
  ├─ TASK 036 ledger integrity: PASS ✅
  ├─ TASK 036 replay determinism: PASS ✅
  └─ Recovery isolated namespace: VERIFIED ✅


NEXT STEPS (TASK 039-S2+)
=========================

  S2: Recovery Classifier + Deterministic Plan Builder
      ├─ Classify failure into taxonomy
      ├─ Build deterministic recovery plan
      └─ Deterministic validation and ranking

  S3: Recovery Simulation Gate
      ├─ Simulate recovery plan impact
      ├─ Measure side effects (read-only)
      └─ Risk assessment before proposal

  S4: Mesh-bound Recovery Proposal Integration
      ├─ Proposal handoff to quorum authority
      ├─ Validate with SafetyGate
      └─ Get quorum approval/rejection

  S5: Recovery Dashboard & Tracing
      ├─ View recovery proposals
      ├─ Query recovery history
      └─ Analyze failure patterns
```
