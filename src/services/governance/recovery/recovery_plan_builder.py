"""
TASK 039-S2: Recovery Plan Builder.

Deterministic plan generation from ClassifiedDiagnosis → RecoveryPlan.

Rules:
- Explicit taxonomy → steps mappings ONLY
- No probabilistic ranking
- No AI input
- No freeform decisions
- No side effects
- No execution
- No mesh/ledger/SQLite mutation
"""

from typing import Mapping, Tuple

from src.services.governance.recovery.recovery_models import (
    RecoveryPlan,
    RecoveryStep,
    RecoveryStepType,
)
from src.services.governance.recovery.recovery_report_hasher import stable_hash
from src.services.governance.recovery.recovery_classifier import (
    ClassifiedDiagnosis,
    RecoveryFailureTaxonomy,
)


# ---------------------------------------------------------------------------
# Explicit deterministic lookup tables
# ---------------------------------------------------------------------------

# taxonomy → ordered step types (canonical, explicit per task spec)
_TAXONOMY_TO_STEPS: Mapping[RecoveryFailureTaxonomy, Tuple[RecoveryStepType, ...]] = {
    RecoveryFailureTaxonomy.NODE_UNHEALTHY: (
        RecoveryStepType.ISOLATE_WORKER,
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
        RecoveryStepType.RESTART_NODE,
    ),
    RecoveryFailureTaxonomy.CACHE_DESYNC: (
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
        RecoveryStepType.REBUILD_SQLITE_PROJECTION,
    ),
    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE: (
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
        RecoveryStepType.ROLLBACK_TO_LEDGER_POINT,
    ),
    RecoveryFailureTaxonomy.QUORUM_DEGRADED: (
        RecoveryStepType.REQUEST_QUORUM_REPAIR,
    ),
    RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION: (
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
        RecoveryStepType.ROLLBACK_TO_LEDGER_POINT,
    ),
    RecoveryFailureTaxonomy.LEDGER_READ_FAILURE: (
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
    ),
    RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION: (
        RecoveryStepType.RUN_REPLAY_VERIFICATION,
    ),
}

# step_type → deterministic duration estimate (seconds)
_STEP_DURATION_SECONDS: Mapping[RecoveryStepType, int] = {
    RecoveryStepType.ISOLATE_WORKER:            5,
    RecoveryStepType.RUN_REPLAY_VERIFICATION:   30,
    RecoveryStepType.REBUILD_SQLITE_PROJECTION: 60,
    RecoveryStepType.REQUEST_QUORUM_REPAIR:     120,
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT:  45,
    RecoveryStepType.RESTART_NODE:              15,
}

# step_type → deterministic reason string (no freeform text)
_STEP_REASON: Mapping[RecoveryStepType, str] = {
    RecoveryStepType.ISOLATE_WORKER:
        "Isolate unhealthy worker to prevent fault propagation.",
    RecoveryStepType.RUN_REPLAY_VERIFICATION:
        "Verify ledger replay produces consistent deterministic state.",
    RecoveryStepType.REBUILD_SQLITE_PROJECTION:
        "Rebuild SQLite projection from authoritative ledger source.",
    RecoveryStepType.REQUEST_QUORUM_REPAIR:
        "Request quorum repair to restore consensus authority.",
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT:
        "Rollback to last known-good ledger checkpoint.",
    RecoveryStepType.RESTART_NODE:
        "Restart node after isolation and verification complete.",
}


# ---------------------------------------------------------------------------
# RecoveryPlanBuilder
# ---------------------------------------------------------------------------

class RecoveryPlanBuilder:
    """
    Deterministic plan builder: ClassifiedDiagnosis → RecoveryPlan.

    Identical diagnosis → identical plan (guaranteed).
    No side effects. No AI. No mesh calls. No ledger writes. No execution.
    """

    def build(
        self,
        classified: ClassifiedDiagnosis,
        target: str = "system",
    ) -> RecoveryPlan:
        """
        Build a deterministic RecoveryPlan from a ClassifiedDiagnosis.

        Args:
            classified: Frozen ClassifiedDiagnosis from RecoveryClassifier.
            target: Recovery target identifier (node ID, service name, etc.).

        Returns:
            RecoveryPlan: Deterministically ordered, frozen plan.
        """
        taxonomy = classified.taxonomy
        step_types = _TAXONOMY_TO_STEPS[taxonomy]

        steps: Tuple[RecoveryStep, ...] = tuple(
            self._build_step(step_type, target, taxonomy)
            for step_type in step_types
        )

        total_duration = sum(
            _STEP_DURATION_SECONDS[RecoveryStepType(s.step_type)]
            for s in steps
        )

        rollback_hash = self._compute_rollback_hash(taxonomy, target)

        return RecoveryPlan(
            steps=steps,
            estimated_duration_seconds=total_duration,
            rollback_plan_hash=rollback_hash,
        )

    def _build_step(
        self,
        step_type: RecoveryStepType,
        target: str,
        taxonomy: RecoveryFailureTaxonomy,
    ) -> RecoveryStep:
        """Build a single deterministic RecoveryStep."""
        return RecoveryStep(
            step_type=step_type.value,
            target=target,
            reason=_STEP_REASON[step_type],
            parameters={"taxonomy": taxonomy.value},
        )

    def _compute_rollback_hash(
        self,
        taxonomy: RecoveryFailureTaxonomy,
        target: str,
    ) -> str:
        """Compute deterministic rollback plan hash."""
        payload = {
            "rollback_for_taxonomy": taxonomy.value,
            "target": target,
            "steps": [s.value for s in _TAXONOMY_TO_STEPS[taxonomy]],
        }
        return stable_hash(payload)
