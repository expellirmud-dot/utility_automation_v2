"""
Recovery subsystem - Deterministic Recovery Proposal Engine.

S1: Frozen models, deterministic hashing, safety gates.
S2: Recovery classifier, failure taxonomy, deterministic plan builder.
S3: Recovery simulation gate.
S4: Recovery handoff boundary.
S5: Recovery observability surface.
NOT execution, NOT mesh integration, NOT ledger mutation.
"""

from src.services.governance.recovery.recovery_models import (
    RecoverySignal,
    RecoveryDiagnosis,
    RecoveryStep,
    RecoveryPlan,
    RecoveryProposal,
    RecoveryReport,
    RecoveryAIAdvice,
    RecoverySignalType,
    RecoverySeverity,
    RecoveryStepType,
    DiagnosisClassification,
    RECOVERY_STEP_PRECEDENCE,
)

from src.services.governance.recovery.recovery_report_hasher import (
    compute_signal_hash,
    compute_diagnosis_hash,
    compute_step_hash,
    compute_plan_hash,
    compute_proposal_hash,
    compute_report_hash,
    verify_signal_hash,
    verify_diagnosis_hash,
    verify_plan_hash,
    verify_proposal_hash,
    verify_report_hash,
    stable_hash,
    canonical_json,
)

from src.services.governance.recovery.recovery_safety import (
    SafetyGate,
    SafeRecoveryProposalBuilder,
    check_recovery_code_safety,
    check_recovery_function_safety,
    enforce_fail_closed,
    RecoverySafetyViolation,
)

from src.services.governance.recovery.recovery_classifier import (
    RecoveryFailureTaxonomy,
    ClassifiedDiagnosis,
    RecoveryClassifier,
)

from src.services.governance.recovery.recovery_plan_builder import (
    RecoveryPlanBuilder,
)

from src.services.governance.recovery.recovery_simulation_gate import (
    RecoverySimulationRiskLevel,
    RecoveryStepSimulation,
    RecoverySimulationReport,
    RecoverySimulationGate,
    RISK_PRECEDENCE,
    STEP_RISK_BY_TYPE,
    STEP_WARNING_CODE_BY_TYPE,
    STEP_WARNING_DETAIL_BY_TYPE,
)

from src.services.governance.recovery.recovery_handoff import (
    RecoveryAuthorityDecision,
    RecoveryAuthorityResponse,
    RecoveryHandoffRequest,
    RecoveryHandoffDecision,
    MeshAuthorityAdapter,
    RecoveryProposalHandoff,
)

from src.services.governance.recovery.recovery_observability import (
    SIGNAL_DETECTED,
    CLASSIFIED,
    PLAN_BUILT,
    SIMULATION_COMPLETED,
    AUTHORITY_HANDOFF,
    AUTHORITY_DECISION,
    RecoveryTimelineEvent,
    RecoveryTimeline,
    RecoveryAnalyticsSnapshot,
    RecoveryArtifactRegistry,
    RecoveryObservabilityService,
)

__all__ = [
    # Models
    "RecoverySignal",
    "RecoveryDiagnosis",
    "RecoveryStep",
    "RecoveryPlan",
    "RecoveryProposal",
    "RecoveryReport",
    "RecoveryAIAdvice",
    # Enums
    "RecoverySignalType",
    "RecoverySeverity",
    "RecoveryStepType",
    "DiagnosisClassification",
    "RECOVERY_STEP_PRECEDENCE",
    # Hashing
    "compute_signal_hash",
    "compute_diagnosis_hash",
    "compute_step_hash",
    "compute_plan_hash",
    "compute_proposal_hash",
    "compute_report_hash",
    "verify_signal_hash",
    "verify_diagnosis_hash",
    "verify_plan_hash",
    "verify_proposal_hash",
    "verify_report_hash",
    "stable_hash",
    "canonical_json",
    # Safety
    "SafetyGate",
    "SafeRecoveryProposalBuilder",
    "check_recovery_code_safety",
    "check_recovery_function_safety",
    "enforce_fail_closed",
    "RecoverySafetyViolation",
    # S2 — Classifier
    "RecoveryFailureTaxonomy",
    "ClassifiedDiagnosis",
    "RecoveryClassifier",
    # S2 — Plan Builder
    "RecoveryPlanBuilder",
    # S3 Simulation Gate
    "RecoverySimulationRiskLevel",
    "RecoveryStepSimulation",
    "RecoverySimulationReport",
    "RecoverySimulationGate",
    "RISK_PRECEDENCE",
    "STEP_RISK_BY_TYPE",
    "STEP_WARNING_CODE_BY_TYPE",
    "STEP_WARNING_DETAIL_BY_TYPE",
    # S4 Handoff
    "RecoveryAuthorityDecision",
    "RecoveryAuthorityResponse",
    "RecoveryHandoffRequest",
    "RecoveryHandoffDecision",
    "MeshAuthorityAdapter",
    "RecoveryProposalHandoff",
    # S5 Observability
    "SIGNAL_DETECTED",
    "CLASSIFIED",
    "PLAN_BUILT",
    "SIMULATION_COMPLETED",
    "AUTHORITY_HANDOFF",
    "AUTHORITY_DECISION",
    "RecoveryTimelineEvent",
    "RecoveryTimeline",
    "RecoveryAnalyticsSnapshot",
    "RecoveryArtifactRegistry",
    "RecoveryObservabilityService",
]
