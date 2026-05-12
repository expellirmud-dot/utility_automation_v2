import inspect

from src.services.governance.recovery.recovery_handoff import (
    BLOCKED_INVALID_AUTHORITY_DECISION,
    BLOCKED_INVALID_PROPOSAL_HASH,
    BLOCKED_INVALID_SIMULATION_HASH,
    BLOCKED_PROPOSAL_SIMULATION_MISMATCH,
    BLOCKED_SIMULATION_NOT_READY,
    BLOCKED_SIMULATION_RISK,
    RecoveryAuthorityDecision,
    RecoveryAuthorityResponse,
    RecoveryHandoffDecision,
    RecoveryProposalHandoff,
    UNKNOWN_AUTHORITY,
)
from src.services.governance.recovery.recovery_models import (
    RecoveryDiagnosis,
    RecoveryPlan,
    RecoveryProposal,
    RecoverySignal,
    RecoverySignalType,
    RecoverySeverity,
    RecoveryStep,
    RecoveryStepType,
    DiagnosisClassification,
)
from src.services.governance.recovery.recovery_report_hasher import stable_hash
from src.services.governance.recovery.recovery_safety import check_recovery_code_safety
from src.services.governance.recovery.recovery_simulation_gate import (
    RecoverySimulationGate,
    RecoverySimulationReport,
    RecoverySimulationRiskLevel,
)


HANDOFF = RecoveryProposalHandoff()
SIMULATION_GATE = RecoverySimulationGate()


class RecordingAdapter:
    def __init__(self, decision="APPROVED", reason="AUTHORITY_APPROVED", authority_name="mesh_authority"):
        self.response = RecoveryAuthorityResponse(
            decision=decision,
            decision_reason=reason,
            authority_name=authority_name,
        )
        self.calls = []

    def evaluate_recovery_proposal(self, request):
        self.calls.append(request)
        return self.response


def make_signal() -> RecoverySignal:
    return RecoverySignal(
        source="test_monitor",
        signal_type=RecoverySignalType.WORKER_CRASH.value,
        severity=RecoverySeverity.HIGH.value,
        epoch=1,
        seq_id=0,
        evidence_hashes=("hash_a",),
    )


def make_diagnosis() -> RecoveryDiagnosis:
    return RecoveryDiagnosis(
        classification=DiagnosisClassification.ISOLATED_FAILURE.value,
        identified_failures=("worker_crash",),
        root_cause_hypothesis="Worker crash requires handoff review.",
        confidence=0.9,
        evidence_count=1,
    )


def make_plan() -> RecoveryPlan:
    step = RecoveryStep(
        step_type=RecoveryStepType.RUN_REPLAY_VERIFICATION.value,
        target="node_1",
        reason="RUN_REPLAY_VERIFICATION_READ_ONLY_CHECK",
        parameters={"scope": "handoff"},
    )
    return RecoveryPlan(
        steps=(step,),
        estimated_duration_seconds=30,
        rollback_plan_hash="rollback_hash",
    )


def make_proposal(proposal_hash: str = "") -> RecoveryProposal:
    return RecoveryProposal(
        signal=make_signal(),
        diagnosis=make_diagnosis(),
        plan=make_plan(),
        reason_for_proposal="handoff review",
        proposal_hash=proposal_hash,
    )


def make_ready_pair():
    proposal = make_proposal()
    simulation = SIMULATION_GATE.simulate_proposal(proposal)
    return proposal, simulation


def make_simulation(
    proposal_hash: str,
    ready: bool = True,
    risk: str = RecoverySimulationRiskLevel.LOW.value,
    simulation_hash: str = "",
) -> RecoverySimulationReport:
    return RecoverySimulationReport(
        proposal_hash=proposal_hash,
        report_hash=None,
        overall_risk=risk,
        ready_for_handoff=ready,
        step_simulations=(),
        warnings=(),
        blocked_reasons=(),
        simulation_hash=simulation_hash,
    )


def test_identical_inputs_produce_identical_decision_hash():
    proposal, simulation = make_ready_pair()
    adapter = RecordingAdapter()

    first = HANDOFF.handoff_proposal(proposal, simulation, adapter)
    second = HANDOFF.handoff_proposal(proposal, simulation, RecordingAdapter())

    assert first == second
    assert first.decision_hash == second.decision_hash
    assert first.ready_for_execution is True
    assert len(adapter.calls) == 1


def test_invalid_proposal_hash_rejected_without_authority_call():
    proposal = make_proposal(proposal_hash="bad_hash")
    simulation = make_simulation(proposal_hash=proposal.proposal_hash)
    adapter = RecordingAdapter()

    decision = HANDOFF.handoff_proposal(proposal, simulation, adapter)

    assert decision.decision == RecoveryAuthorityDecision.REJECTED.value
    assert decision.ready_for_execution is False
    assert decision.blocked_reason_codes == (BLOCKED_INVALID_PROPOSAL_HASH,)
    assert adapter.calls == []


def test_invalid_simulation_hash_rejected():
    proposal, simulation = make_ready_pair()
    invalid_simulation = RecoverySimulationReport(
        proposal_hash=simulation.proposal_hash,
        report_hash=simulation.report_hash,
        overall_risk=simulation.overall_risk,
        ready_for_handoff=simulation.ready_for_handoff,
        step_simulations=simulation.step_simulations,
        warnings=simulation.warnings,
        blocked_reasons=simulation.blocked_reasons,
        simulation_hash="bad_hash",
    )

    decision = HANDOFF.handoff_proposal(proposal, invalid_simulation, RecordingAdapter())

    assert decision.decision == RecoveryAuthorityDecision.REJECTED.value
    assert decision.blocked_reason_codes == (BLOCKED_INVALID_SIMULATION_HASH,)


def test_blocked_simulation_risk_rejected_without_authority_call():
    proposal = make_proposal()
    simulation = make_simulation(
        proposal_hash=proposal.proposal_hash,
        ready=False,
        risk=RecoverySimulationRiskLevel.BLOCKED.value,
    )
    adapter = RecordingAdapter()

    decision = HANDOFF.handoff_proposal(proposal, simulation, adapter)

    assert decision.decision == RecoveryAuthorityDecision.REJECTED.value
    assert decision.ready_for_execution is False
    assert decision.blocked_reason_codes == tuple(sorted((
        BLOCKED_SIMULATION_NOT_READY,
        BLOCKED_SIMULATION_RISK,
    )))
    assert adapter.calls == []


def test_mismatched_proposal_and_simulation_hashes_rejected():
    proposal = make_proposal()
    simulation = make_simulation(proposal_hash="other_proposal_hash")

    decision = HANDOFF.handoff_proposal(proposal, simulation, RecordingAdapter())

    assert decision.decision == RecoveryAuthorityDecision.REJECTED.value
    assert decision.blocked_reason_codes == (BLOCKED_PROPOSAL_SIMULATION_MISMATCH,)


def test_authority_decision_normalization_is_deterministic():
    proposal, simulation = make_ready_pair()

    hashes = {
        HANDOFF.handoff_proposal(
            proposal,
            simulation,
            RecordingAdapter(decision=value, reason="same", authority_name="same_authority"),
        ).decision_hash
        for value in ("approved", "APPROVED", "Approved")
    }

    assert len(hashes) == 1


def test_unknown_authority_name_fallback():
    proposal, simulation = make_ready_pair()

    blank = HANDOFF.handoff_proposal(
        proposal,
        simulation,
        RecordingAdapter(decision="APPROVED", authority_name=""),
    )
    missing = HANDOFF.handoff_proposal(
        proposal,
        simulation,
        RecordingAdapter(decision="APPROVED", authority_name=None),
    )

    assert blank.authority_name == UNKNOWN_AUTHORITY
    assert missing.authority_name == UNKNOWN_AUTHORITY


def test_rejected_and_deferred_are_not_ready_for_execution():
    proposal, simulation = make_ready_pair()

    rejected = HANDOFF.handoff_proposal(proposal, simulation, RecordingAdapter(decision="REJECTED"))
    deferred = HANDOFF.handoff_proposal(proposal, simulation, RecordingAdapter(decision="DEFERRED"))

    assert rejected.ready_for_execution is False
    assert deferred.ready_for_execution is False


def test_invalid_authority_decision_fails_closed():
    proposal, simulation = make_ready_pair()

    decision = HANDOFF.handoff_proposal(
        proposal,
        simulation,
        RecordingAdapter(decision="ALLOW", reason="not supported"),
    )

    assert decision.decision == RecoveryAuthorityDecision.REJECTED.value
    assert decision.ready_for_execution is False
    assert decision.blocked_reason_codes == (BLOCKED_INVALID_AUTHORITY_DECISION,)


def test_handoff_decision_is_frozen_and_hashable():
    proposal, simulation = make_ready_pair()
    decision = HANDOFF.handoff_proposal(proposal, simulation, RecordingAdapter())

    assert isinstance(decision, RecoveryHandoffDecision)
    assert decision.decision_hash == stable_hash(decision.to_payload(include_hash=False))
    assert decision.authority_response_hash


def test_handoff_module_has_no_direct_runtime_coupling_or_local_actions():
    import src.services.governance.recovery.recovery_handoff as module

    source = inspect.getsource(module)
    assert "MeshOrchestrator" not in source
    assert "execute_plan" not in source
    assert "apply_recovery" not in source
    assert "run_recovery" not in source

    is_safe, violations = check_recovery_code_safety(source)
    assert is_safe, "\n".join(violations)


def test_safety_gate_rejects_s4_forbidden_fixtures():
    fixtures = [
        "MeshOrchestrator()",
        "execute_plan(plan)",
        "apply_recovery(plan)",
        "run_recovery(plan)",
        "sqlite3.connect(path)",
    ]

    for code in fixtures:
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert violations
