"""
Recovery subsystem - Deterministic Recovery Proposal Engine.

S1: Frozen models, deterministic hashing, safety gates.
S2: Recovery classifier, failure taxonomy, deterministic plan builder.
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
]
