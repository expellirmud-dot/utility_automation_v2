import inspect

import pytest

from src.services.governance.recovery.recovery_models import (
    RecoveryAIAdvice,
    RecoveryDiagnosis,
    RecoveryPlan,
    RecoveryProposal,
    RecoveryReport,
    RecoverySignal,
    RecoverySignalType,
    RecoverySeverity,
    RecoveryStep,
    RecoveryStepType,
    DiagnosisClassification,
)
from src.services.governance.recovery.recovery_report_hasher import compute_proposal_hash
from src.services.governance.recovery.recovery_safety import check_recovery_code_safety
from src.services.governance.recovery.recovery_simulation_gate import (
    RISK_PRECEDENCE,
    STEP_RISK_BY_TYPE,
    STEP_WARNING_CODE_BY_TYPE,
    STEP_WARNING_DETAIL_BY_TYPE,
    RecoverySimulationGate,
    RecoverySimulationRiskLevel,
)


GATE = RecoverySimulationGate()


class UnknownStep:
    step_type = "UNKNOWN_STEP"
    target = "unknown"
    reason = "unknown"
    parameters = {}

    def sort_key(self):
        return (99, self.target, self.reason, "")


def make_signal() -> RecoverySignal:
    return RecoverySignal(
        source="test_monitor",
        signal_type=RecoverySignalType.WORKER_CRASH.value,
        severity=RecoverySeverity.HIGH.value,
        epoch=1,
        seq_id=0,
        evidence_hashes=("hash_b", "hash_a"),
    )


def make_diagnosis() -> RecoveryDiagnosis:
    return RecoveryDiagnosis(
        classification=DiagnosisClassification.ISOLATED_FAILURE.value,
        identified_failures=("worker_crash",),
        root_cause_hypothesis="Worker crash requires deterministic recovery review.",
        confidence=0.9,
        evidence_count=2,
    )


def make_step(step_type: RecoveryStepType, target: str = "node_1") -> RecoveryStep:
    return RecoveryStep(
        step_type=step_type.value,
        target=target,
        reason=STEP_WARNING_DETAIL_BY_TYPE[step_type],
        parameters={"step": step_type.value},
    )


def make_plan(steps) -> RecoveryPlan:
    return RecoveryPlan(
        steps=tuple(steps),
        estimated_duration_seconds=60,
        rollback_plan_hash="rollback_hash",
    )


def make_proposal(plan: RecoveryPlan, proposal_hash: str = "") -> RecoveryProposal:
    return RecoveryProposal(
        signal=make_signal(),
        diagnosis=make_diagnosis(),
        plan=plan,
        reason_for_proposal="deterministic recovery review",
        proposal_hash=proposal_hash,
    )


def test_identical_proposal_produces_identical_simulation_report():
    proposal = make_proposal(make_plan([
        make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION),
        make_step(RecoveryStepType.RESTART_NODE),
    ]))

    first = GATE.simulate_proposal(proposal)
    second = GATE.simulate_proposal(proposal)

    assert first == second
    assert first.simulation_hash == second.simulation_hash
    assert first.ready_for_handoff is True


def test_reordered_input_steps_with_same_canonical_plan_have_same_simulation_hash():
    replay = make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION)
    restart = make_step(RecoveryStepType.RESTART_NODE)
    first = make_proposal(make_plan([restart, replay]))
    second = make_proposal(make_plan([replay, restart]))

    assert first.plan.steps == second.plan.steps
    assert first.proposal_hash == second.proposal_hash
    assert GATE.simulate_proposal(first).simulation_hash == GATE.simulate_proposal(second).simulation_hash


def test_simulation_hash_uses_proposal_identity_not_report_identity():
    proposal = make_proposal(make_plan([make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION)]))
    report = RecoveryReport(proposal=proposal)

    from_proposal = GATE.simulate_proposal(proposal)
    from_report = GATE.simulate_report(report)

    assert from_report.report_hash == report.report_hash
    assert from_proposal.simulation_hash == from_report.simulation_hash


def test_step_risk_warning_mapping_covers_all_step_types():
    for step_type in RecoveryStepType:
        assert step_type in STEP_RISK_BY_TYPE
        assert step_type in STEP_WARNING_CODE_BY_TYPE
        assert step_type in STEP_WARNING_DETAIL_BY_TYPE
        assert STEP_RISK_BY_TYPE[step_type] in RecoverySimulationRiskLevel
        assert STEP_WARNING_CODE_BY_TYPE[step_type]
        assert STEP_WARNING_DETAIL_BY_TYPE[step_type]


def test_mixed_step_plan_uses_numeric_risk_precedence():
    proposal = make_proposal(make_plan([
        make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION),
        make_step(RecoveryStepType.REBUILD_SQLITE_PROJECTION),
        make_step(RecoveryStepType.REQUEST_QUORUM_REPAIR),
    ]))

    report = GATE.simulate_proposal(proposal)

    assert RISK_PRECEDENCE[RecoverySimulationRiskLevel.LOW] == 1
    assert RISK_PRECEDENCE[RecoverySimulationRiskLevel.MEDIUM] == 2
    assert RISK_PRECEDENCE[RecoverySimulationRiskLevel.HIGH] == 3
    assert RISK_PRECEDENCE[RecoverySimulationRiskLevel.BLOCKED] == 4
    assert report.overall_risk == RecoverySimulationRiskLevel.HIGH.value


def test_empty_plan_blocks():
    proposal = make_proposal(make_plan([]))

    report = GATE.simulate_proposal(proposal)

    assert report.ready_for_handoff is False
    assert report.overall_risk == RecoverySimulationRiskLevel.BLOCKED.value
    assert report.blocked_reasons == ("BLOCKED_EMPTY_PLAN",)


def test_invalid_proposal_hash_blocks():
    proposal = make_proposal(
        make_plan([make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION)]),
        proposal_hash="invalid",
    )

    report = GATE.simulate_proposal(proposal)

    assert report.ready_for_handoff is False
    assert "BLOCKED_INVALID_PROPOSAL_HASH" in report.blocked_reasons
    assert proposal.proposal_hash != compute_proposal_hash(proposal)


def test_invalid_report_hash_blocks():
    proposal = make_proposal(make_plan([make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION)]))
    report = RecoveryReport(proposal=proposal, report_hash="invalid")

    simulation = GATE.simulate_report(report)

    assert simulation.ready_for_handoff is False
    assert simulation.report_hash == "invalid"
    assert "BLOCKED_INVALID_REPORT_HASH" in simulation.blocked_reasons


def test_multiple_blocked_reasons_are_sorted():
    proposal = make_proposal(make_plan([UnknownStep()]), proposal_hash="invalid")
    report = RecoveryReport(proposal=proposal, report_hash="invalid")

    simulation = GATE.simulate_report(report)

    assert simulation.ready_for_handoff is False
    assert len(simulation.blocked_reasons) == 3
    assert simulation.blocked_reasons == tuple(sorted(simulation.blocked_reasons))


def test_ai_advice_is_excluded_from_simulation_hash():
    proposal = make_proposal(make_plan([make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION)]))
    first = RecoveryReport(
        proposal=proposal,
        ai_advice=RecoveryAIAdvice(warnings=("z",), notes=("first",), model_used="model_a"),
    )
    second = RecoveryReport(
        proposal=proposal,
        ai_advice=RecoveryAIAdvice(warnings=("a",), notes=("second",), model_used="model_b"),
    )

    assert first.ai_advice != second.ai_advice
    assert GATE.simulate_report(first).simulation_hash == GATE.simulate_report(second).simulation_hash


def test_warnings_are_sorted():
    proposal = make_proposal(make_plan([
        make_step(RecoveryStepType.RESTART_NODE),
        make_step(RecoveryStepType.ISOLATE_WORKER),
        make_step(RecoveryStepType.RUN_REPLAY_VERIFICATION),
    ]))

    report = GATE.simulate_proposal(proposal)

    assert report.warnings == tuple(sorted(report.warnings))


def test_s3_module_has_no_forbidden_side_effects():
    import src.services.governance.recovery.recovery_simulation_gate as module

    source = inspect.getsource(module)
    is_safe, violations = check_recovery_code_safety(source)

    assert is_safe, "\n".join(violations)
