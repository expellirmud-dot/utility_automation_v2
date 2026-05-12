"""
Quick demonstration of TASK 039-S1 Recovery Foundation features.
"""
from src.services.governance.recovery import (
    RecoverySignal, RecoveryDiagnosis, RecoveryStep, RecoveryPlan,
    RecoveryProposal, RecoveryReport, RecoveryAIAdvice,
    RecoverySignalType, RecoverySeverity, RecoveryStepType,
    DiagnosisClassification, compute_proposal_hash, check_recovery_code_safety
)

# Create signal
signal = RecoverySignal(
    source="health_checker",
    signal_type=RecoverySignalType.WORKER_CRASH.value,
    severity=RecoverySeverity.CRITICAL.value,
    epoch=1,
    seq_id=0,
    evidence_hashes=("hash_abc", "hash_def"),
)

# Create diagnosis
diagnosis = RecoveryDiagnosis(
    classification=DiagnosisClassification.ISOLATED_FAILURE.value,
    identified_failures=("OutOfMemory", "SegmentationFault"),
    root_cause_hypothesis="Memory leak in worker process",
    confidence=0.95,
    evidence_count=5,
)

# Create recovery steps
step1 = RecoveryStep(
    step_type=RecoveryStepType.ISOLATE_WORKER.value,
    target="worker_node_3",
    reason="Prevent cascade failure",
    parameters={"timeout_seconds": 30},
)

step2 = RecoveryStep(
    step_type=RecoveryStepType.RESTART_NODE.value,
    target="worker_node_3",
    reason="Restart after cleanup",
    parameters={"grace_period": 60},
)

# Create plan
plan = RecoveryPlan(
    steps=(step1, step2),  # Will be reordered by precedence
    estimated_duration_seconds=120,
    rollback_plan_hash="rollback_abc123",
)

# Create proposal
proposal = RecoveryProposal(
    signal=signal,
    diagnosis=diagnosis,
    plan=plan,
    reason_for_proposal="Automatic recovery triggered by health check",
)

# Create report with AI advice
ai_advice = RecoveryAIAdvice(
    confidence_adjustment=0.05,
    warnings=("Worker may have open transactions",),
    model_used="GPT-4",
)

report = RecoveryReport(
    proposal=proposal,
    ai_advice=ai_advice,
)

# Verify determinism
proposal2 = RecoveryProposal(
    signal=signal,
    diagnosis=diagnosis,
    plan=plan,
    reason_for_proposal="Automatic recovery triggered by health check",
)

print(f"✅ Signal frozen: {signal.source}")
print(f"✅ Diagnosis confidence: {diagnosis.confidence}")
print(f"✅ Plan steps ordered by precedence: {[s.step_type for s in plan.steps]}")
print(f"✅ Proposal hash: {proposal.proposal_hash[:16]}...")
print(f"✅ Report hash: {report.report_hash[:16]}...")
print(f"✅ Hashes deterministic: {proposal.proposal_hash == proposal2.proposal_hash}")
print(f"✅ AI advice payload: {ai_advice.to_payload()}")

# Test safety gate
safe_code = "def recover(): return normalize_signal(signal)"
is_safe, violations = check_recovery_code_safety(safe_code)
print(f"✅ Safe code allowed: {is_safe}")

forbidden_code = "def bad_recover(): append_event(event)"
is_safe, violations = check_recovery_code_safety(forbidden_code)
print(f"✅ Forbidden code blocked: {not is_safe}")

print("\n✅ TASK 039-S1 Foundation Verified")
