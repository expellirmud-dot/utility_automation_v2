"""
Deterministic Recovery Foundation Models.

Frozen, immutable models for recovery signal detection and proposal generation.
AI advice is strictly separated and excluded from deterministic hashes.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple
from enum import Enum


class RecoverySignalType(str, Enum):
    """Signal types that trigger recovery analysis."""
    HEALTH_CHECK_FAILURE = "HEALTH_CHECK_FAILURE"
    LEDGER_DIVERGENCE = "LEDGER_DIVERGENCE"
    QUORUM_LOSS = "QUORUM_LOSS"
    WORKER_CRASH = "WORKER_CRASH"
    SQLITE_CORRUPTION = "SQLITE_CORRUPTION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    REPLICATION_LAG = "REPLICATION_LAG"
    TIMEOUT_DETECTED = "TIMEOUT_DETECTED"


class RecoverySeverity(str, Enum):
    """Severity levels for recovery signals."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecoveryStepType(str, Enum):
    """Recovery action types with explicit precedence."""
    ISOLATE_WORKER = "ISOLATE_WORKER"
    RUN_REPLAY_VERIFICATION = "RUN_REPLAY_VERIFICATION"
    REBUILD_SQLITE_PROJECTION = "REBUILD_SQLITE_PROJECTION"
    REQUEST_QUORUM_REPAIR = "REQUEST_QUORUM_REPAIR"
    ROLLBACK_TO_LEDGER_POINT = "ROLLBACK_TO_LEDGER_POINT"
    RESTART_NODE = "RESTART_NODE"


# Explicit step precedence (lower index = higher priority)
RECOVERY_STEP_PRECEDENCE = [
    RecoveryStepType.ISOLATE_WORKER,
    RecoveryStepType.RUN_REPLAY_VERIFICATION,
    RecoveryStepType.REBUILD_SQLITE_PROJECTION,
    RecoveryStepType.REQUEST_QUORUM_REPAIR,
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT,
    RecoveryStepType.RESTART_NODE,
]


class DiagnosisClassification(str, Enum):
    """Classification of diagnosed issue."""
    ISOLATED_FAILURE = "ISOLATED_FAILURE"
    SYSTEMIC_DEGRADATION = "SYSTEMIC_DEGRADATION"
    DISTRIBUTED_SPLIT = "DISTRIBUTED_SPLIT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RecoverySignal:
    """
    Input signal indicating a potential recovery need.
    Deterministically normalized, no arbitrary freeform objects.
    """
    source: str  # e.g., "health_monitor", "replica_check", "consensus_layer"
    signal_type: str  # Must be RecoverySignalType value
    severity: str  # Must be RecoverySeverity value
    epoch: int  # Deterministic epoch counter
    seq_id: int  # Sequence in epoch
    evidence_hashes: Tuple[str, ...]  # SHA256 hashes of evidence
    metadata: Mapping[str, Any] = field(default_factory=dict)  # Normalized dict

    def __post_init__(self):
        """Normalize and validate signal."""
        # Validate enums
        if self.signal_type not in [e.value for e in RecoverySignalType]:
            raise ValueError(f"Invalid signal_type: {self.signal_type}")
        if self.severity not in [e.value for e in RecoverySeverity]:
            raise ValueError(f"Invalid severity: {self.severity}")

        # Sort evidence hashes for determinism
        sorted_hashes = tuple(sorted(self.evidence_hashes))
        object.__setattr__(self, "evidence_hashes", sorted_hashes)

        # Freeze metadata
        if self.metadata:
            frozen_meta = self._freeze_dict(self.metadata)
            object.__setattr__(self, "metadata", frozen_meta)

    @staticmethod
    def _freeze_dict(d: Mapping[str, Any]) -> Mapping[str, Any]:
        """Recursively freeze a dict for determinism."""
        result = {}
        for k in sorted(d.keys()):
            v = d[k]
            if isinstance(v, dict):
                result[k] = RecoverySignal._freeze_dict(v)
            elif isinstance(v, list):
                result[k] = tuple(RecoverySignal._freeze_dict(item) if isinstance(item, dict) else item for item in v)
            else:
                result[k] = v
        return result


@dataclass(frozen=True)
class RecoveryStep:
    """
    A single recovery action proposal with explicit precedence ordering.
    """
    step_type: str  # Must be RecoveryStepType value
    target: str  # e.g., "worker_1", "ledger", "sqlite_cache"
    reason: str  # Human-readable reason
    parameters: Mapping[str, Any] = field(default_factory=dict)
    _precedence_index: int = field(init=False, repr=False)

    def __post_init__(self):
        """Validate and set precedence."""
        if self.step_type not in [e.value for e in RecoveryStepType]:
            raise ValueError(f"Invalid step_type: {self.step_type}")

        # Set precedence index based on type
        try:
            idx = RECOVERY_STEP_PRECEDENCE.index(RecoveryStepType(self.step_type))
        except ValueError:
            idx = len(RECOVERY_STEP_PRECEDENCE)

        object.__setattr__(self, "_precedence_index", idx)

        # Freeze parameters
        if self.parameters:
            frozen_params = RecoverySignal._freeze_dict(self.parameters)
            object.__setattr__(self, "parameters", frozen_params)

    def sort_key(self) -> Tuple:
        """Key for deterministic sorting of recovery steps."""
        return (
            self._precedence_index,
            self.target,
            self.reason,
            self._canonical_params_hash(),
        )

    def _canonical_params_hash(self) -> str:
        """Canonical hash of parameters for deterministic ordering."""
        import json
        import hashlib
        from src.services.governance.policy_graph.policy_version import canonical_json

        canon = canonical_json(self.parameters) if self.parameters else ""
        return hashlib.sha256(canon.encode()).hexdigest()


@dataclass(frozen=True)
class RecoveryDiagnosis:
    """
    Analysis of the failure, separate from remedy.
    """
    classification: str  # Must be DiagnosisClassification value
    identified_failures: Tuple[str, ...]  # List of detected issues
    root_cause_hypothesis: str
    confidence: float  # 0.0 to 1.0
    evidence_count: int

    def __post_init__(self):
        """Validate diagnosis."""
        if self.classification not in [e.value for e in DiagnosisClassification]:
            raise ValueError(f"Invalid classification: {self.classification}")
        
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

        # Sort failures for determinism
        sorted_failures = tuple(sorted(self.identified_failures))
        object.__setattr__(self, "identified_failures", sorted_failures)


@dataclass(frozen=True)
class RecoveryPlan:
    """
    Deterministically ordered sequence of recovery step proposals.
    """
    steps: Tuple[RecoveryStep, ...]
    estimated_duration_seconds: int
    rollback_plan_hash: str  # Hash of rollback procedure

    def __post_init__(self):
        """Sort steps by deterministic precedence."""
        sorted_steps = tuple(sorted(self.steps, key=lambda s: s.sort_key()))
        object.__setattr__(self, "steps", sorted_steps)


@dataclass(frozen=True)
class RecoveryProposal:
    """
    Complete recovery proposal without execution or AI advice.
    Excludes AI advice from all hashes.
    """
    signal: RecoverySignal
    diagnosis: RecoveryDiagnosis
    plan: RecoveryPlan
    reason_for_proposal: str
    proposal_hash: str = field(default="")

    def __post_init__(self):
        """Compute deterministic proposal hash (excluding AI advice)."""
        if not self.proposal_hash:
            from src.services.governance.recovery.recovery_report_hasher import compute_proposal_hash
            computed_hash = compute_proposal_hash(self)
            object.__setattr__(self, "proposal_hash", computed_hash)


@dataclass(frozen=True)
class RecoveryAIAdvice:
    """
    Separate AI-generated advice, never included in deterministic hashes.
    """
    confidence_adjustment: float = 0.0  # Confidence delta
    suggested_alternatives: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    model_used: str = ""

    def __post_init__(self):
        """Sort tuples for consistent representation."""
        object.__setattr__(self, "suggested_alternatives", tuple(sorted(self.suggested_alternatives)))
        object.__setattr__(self, "warnings", tuple(sorted(self.warnings)))
        object.__setattr__(self, "notes", tuple(sorted(self.notes)))

    def to_payload(self) -> dict:
        """Serialize for logging/display (not for hashing)."""
        return {
            "confidence_adjustment": self.confidence_adjustment,
            "suggested_alternatives": list(self.suggested_alternatives),
            "warnings": list(self.warnings),
            "notes": list(self.notes),
            "model_used": self.model_used,
        }


@dataclass(frozen=True)
class RecoveryReport:
    """
    Final recovery report with proposal, excluding AI advice from hashes.
    """
    proposal: RecoveryProposal
    report_hash: str = field(default="")
    ai_advice: Optional[RecoveryAIAdvice] = None

    def __post_init__(self):
        """Compute deterministic report hash (excluding AI advice)."""
        if not self.report_hash:
            from src.services.governance.recovery.recovery_report_hasher import compute_report_hash
            computed_hash = compute_report_hash(self)
            object.__setattr__(self, "report_hash", computed_hash)

    def to_payload(self, include_ai_advice: bool = False) -> dict:
        """Serialize, optionally including AI advice."""
        payload = {
            "proposal": self._proposal_to_payload(),
            "report_hash": self.report_hash,
        }
        if include_ai_advice and self.ai_advice:
            payload["ai_advice"] = self.ai_advice.to_payload()
        return payload

    def _proposal_to_payload(self) -> dict:
        """Convert proposal to payload."""
        return {
            "signal": {
                "source": self.proposal.signal.source,
                "signal_type": self.proposal.signal.signal_type,
                "severity": self.proposal.signal.severity,
                "epoch": self.proposal.signal.epoch,
                "seq_id": self.proposal.signal.seq_id,
                "evidence_hashes": list(self.proposal.signal.evidence_hashes),
                "metadata": dict(self.proposal.signal.metadata),
            },
            "diagnosis": {
                "classification": self.proposal.diagnosis.classification,
                "identified_failures": list(self.proposal.diagnosis.identified_failures),
                "root_cause_hypothesis": self.proposal.diagnosis.root_cause_hypothesis,
                "confidence": self.proposal.diagnosis.confidence,
                "evidence_count": self.proposal.diagnosis.evidence_count,
            },
            "plan": {
                "steps": [self._step_to_payload(s) for s in self.proposal.plan.steps],
                "estimated_duration_seconds": self.proposal.plan.estimated_duration_seconds,
                "rollback_plan_hash": self.proposal.plan.rollback_plan_hash,
            },
            "reason_for_proposal": self.proposal.reason_for_proposal,
            "proposal_hash": self.proposal.proposal_hash,
        }

    @staticmethod
    def _step_to_payload(step: RecoveryStep) -> dict:
        """Convert a step to payload."""
        return {
            "step_type": step.step_type,
            "target": step.target,
            "reason": step.reason,
            "parameters": dict(step.parameters),
        }
