"""
TASK 039-S2: Recovery Classifier.

Deterministic classification of RecoverySignal → ClassifiedDiagnosis.

Rules:
- Explicit deterministic mappings ONLY
- No probabilistic ranking
- No AI-derived classifications
- No freeform runtime decisions
- No authority boundary crossing
- No side effects
"""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from src.services.governance.recovery.recovery_models import (
    RecoveryDiagnosis,
    RecoverySignal,
    DiagnosisClassification,
    RecoverySignalType,
)
from src.services.governance.recovery.recovery_report_hasher import compute_signal_hash


# ---------------------------------------------------------------------------
# S2 Failure Taxonomy
# ---------------------------------------------------------------------------

class RecoveryFailureTaxonomy(str, Enum):
    """Deterministic failure taxonomy for S2 classification."""
    NODE_UNHEALTHY = "NODE_UNHEALTHY"
    QUORUM_DEGRADED = "QUORUM_DEGRADED"
    REPLAY_DIVERGENCE = "REPLAY_DIVERGENCE"
    CACHE_DESYNC = "CACHE_DESYNC"
    POLICY_GRAPH_CORRUPTION = "POLICY_GRAPH_CORRUPTION"
    SIMULATION_WARNING_ESCALATION = "SIMULATION_WARNING_ESCALATION"
    LEDGER_READ_FAILURE = "LEDGER_READ_FAILURE"


# ---------------------------------------------------------------------------
# Explicit deterministic lookup tables (no runtime inference)
# ---------------------------------------------------------------------------

# signal_type → taxonomy (explicit, no fallback inference)
_SIGNAL_TO_TAXONOMY: Mapping[str, RecoveryFailureTaxonomy] = {
    RecoverySignalType.HEALTH_CHECK_FAILURE.value: RecoveryFailureTaxonomy.NODE_UNHEALTHY,
    RecoverySignalType.WORKER_CRASH.value:         RecoveryFailureTaxonomy.NODE_UNHEALTHY,
    RecoverySignalType.TIMEOUT_DETECTED.value:     RecoveryFailureTaxonomy.NODE_UNHEALTHY,
    RecoverySignalType.QUORUM_LOSS.value:          RecoveryFailureTaxonomy.QUORUM_DEGRADED,
    RecoverySignalType.LEDGER_DIVERGENCE.value:    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE,
    RecoverySignalType.SQLITE_CORRUPTION.value:    RecoveryFailureTaxonomy.CACHE_DESYNC,
    RecoverySignalType.REPLICATION_LAG.value:      RecoveryFailureTaxonomy.CACHE_DESYNC,
    RecoverySignalType.POLICY_VIOLATION.value:     RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION,
}

# taxonomy → DiagnosisClassification (explicit)
_TAXONOMY_TO_CLASSIFICATION: Mapping[RecoveryFailureTaxonomy, DiagnosisClassification] = {
    RecoveryFailureTaxonomy.NODE_UNHEALTHY:                DiagnosisClassification.ISOLATED_FAILURE,
    RecoveryFailureTaxonomy.QUORUM_DEGRADED:               DiagnosisClassification.SYSTEMIC_DEGRADATION,
    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE:             DiagnosisClassification.DISTRIBUTED_SPLIT,
    RecoveryFailureTaxonomy.CACHE_DESYNC:                  DiagnosisClassification.ISOLATED_FAILURE,
    RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION:       DiagnosisClassification.SYSTEMIC_DEGRADATION,
    RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION: DiagnosisClassification.ISOLATED_FAILURE,
    RecoveryFailureTaxonomy.LEDGER_READ_FAILURE:           DiagnosisClassification.SYSTEMIC_DEGRADATION,
}

# taxonomy → deterministic confidence (explicit, not probabilistic)
_TAXONOMY_CONFIDENCE: Mapping[RecoveryFailureTaxonomy, float] = {
    RecoveryFailureTaxonomy.NODE_UNHEALTHY:                0.95,
    RecoveryFailureTaxonomy.QUORUM_DEGRADED:               0.90,
    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE:             0.90,
    RecoveryFailureTaxonomy.CACHE_DESYNC:                  0.85,
    RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION:       0.90,
    RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION: 0.70,
    RecoveryFailureTaxonomy.LEDGER_READ_FAILURE:           0.85,
}

# taxonomy → deterministic hypothesis string
_TAXONOMY_HYPOTHESIS: Mapping[RecoveryFailureTaxonomy, str] = {
    RecoveryFailureTaxonomy.NODE_UNHEALTHY:
        "Node health degraded; isolation and replay verification required.",
    RecoveryFailureTaxonomy.QUORUM_DEGRADED:
        "Quorum membership below threshold; quorum repair required.",
    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE:
        "Ledger replay produces divergent state; rollback to known-good point required.",
    RecoveryFailureTaxonomy.CACHE_DESYNC:
        "SQLite projection out of sync with ledger; projection rebuild required.",
    RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION:
        "Policy graph inconsistent with ledger; replay verification and rollback required.",
    RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION:
        "Simulation detected warning conditions requiring operator attention.",
    RecoveryFailureTaxonomy.LEDGER_READ_FAILURE:
        "Ledger read failed; replay verification required to restore consistency.",
}


# ---------------------------------------------------------------------------
# ClassifiedDiagnosis — frozen output of the classifier
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClassifiedDiagnosis:
    """
    Deterministic output of RecoveryClassifier.

    Pairs taxonomy + diagnosis + signal traceability hash.
    Frozen, immutable. No AI. No runtime decisions.
    """
    taxonomy: RecoveryFailureTaxonomy
    diagnosis: RecoveryDiagnosis
    signal_hash: str  # SHA256 of input signal for traceability

    def __post_init__(self):
        """Validate taxonomy and diagnosis classification are consistent."""
        expected = _TAXONOMY_TO_CLASSIFICATION[self.taxonomy].value
        if self.diagnosis.classification != expected:
            raise ValueError(
                f"Taxonomy {self.taxonomy} requires classification "
                f"'{expected}', got '{self.diagnosis.classification}'"
            )


# ---------------------------------------------------------------------------
# RecoveryClassifier
# ---------------------------------------------------------------------------

class RecoveryClassifier:
    """
    Deterministic classifier: RecoverySignal → ClassifiedDiagnosis.

    Identical signal → identical diagnosis (guaranteed).
    No side effects. No AI. No mesh calls. No ledger writes.
    """

    # Metadata key that triggers SIMULATION_WARNING_ESCALATION override.
    # Deterministic: same metadata → same taxonomy.
    _SIMULATION_ESCALATION_KEY = "simulation_escalation"

    def classify(self, signal: RecoverySignal) -> ClassifiedDiagnosis:
        """
        Classify a RecoverySignal into a ClassifiedDiagnosis.

        Args:
            signal: Validated, frozen RecoverySignal from S1.

        Returns:
            ClassifiedDiagnosis: frozen, deterministic output.
        """
        taxonomy = self._resolve_taxonomy(signal)
        diagnosis = self._build_diagnosis(taxonomy, signal)
        signal_hash = compute_signal_hash(signal)

        return ClassifiedDiagnosis(
            taxonomy=taxonomy,
            diagnosis=diagnosis,
            signal_hash=signal_hash,
        )

    def _resolve_taxonomy(self, signal: RecoverySignal) -> RecoveryFailureTaxonomy:
        """
        Map signal → taxonomy via explicit lookup table.

        Simulation escalation override is checked first (deterministic metadata key).
        Unknown signal types fall back to LEDGER_READ_FAILURE (fail-safe).
        """
        # Deterministic simulation escalation override
        if signal.metadata.get(self._SIMULATION_ESCALATION_KEY) is True:
            return RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION

        # Explicit signal_type → taxonomy table
        taxonomy = _SIGNAL_TO_TAXONOMY.get(signal.signal_type)
        if taxonomy is not None:
            return taxonomy

        # Fail-safe: unknown signal → most conservative action
        return RecoveryFailureTaxonomy.LEDGER_READ_FAILURE

    def _build_diagnosis(
        self,
        taxonomy: RecoveryFailureTaxonomy,
        signal: RecoverySignal,
    ) -> RecoveryDiagnosis:
        """Build deterministic RecoveryDiagnosis from taxonomy + signal."""
        classification = _TAXONOMY_TO_CLASSIFICATION[taxonomy]
        confidence = _TAXONOMY_CONFIDENCE[taxonomy]
        hypothesis = _TAXONOMY_HYPOTHESIS[taxonomy]

        # identified_failures: deterministic tuple from taxonomy + signal type
        identified_failures: tuple = (
            taxonomy.value,
            f"signal:{signal.signal_type}",
        )

        return RecoveryDiagnosis(
            classification=classification.value,
            identified_failures=identified_failures,
            root_cause_hypothesis=hypothesis,
            confidence=confidence,
            evidence_count=len(signal.evidence_hashes),
        )
