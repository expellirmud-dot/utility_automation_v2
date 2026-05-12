import inspect

from src.services.governance.recovery.recovery_handoff import (
    RecoveryAuthorityDecision,
    RecoveryHandoffDecision,
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
from src.services.governance.recovery.recovery_observability import (
    AUTHORITY_DECISION,
    AUTHORITY_HANDOFF,
    CLASSIFIED,
    EVENT_CLASSIFICATION,
    EVENT_DECISION,
    EVENT_HANDOFF,
    EVENT_PLAN,
    EVENT_SIGNAL,
    EVENT_SIMULATION,
    PLAN_BUILT,
    SIGNAL_DETECTED,
    SIMULATION_COMPLETED,
    RecoveryArtifactRegistry,
    RecoveryObservabilityService,
)
from src.services.governance.recovery.recovery_report_hasher import stable_hash
from src.services.governance.recovery.recovery_safety import check_recovery_code_safety
from src.services.governance.recovery.recovery_simulation_gate import (
    RecoverySimulationReport,
    RecoverySimulationRiskLevel,
)


def make_signal(index: int) -> RecoverySignal:
    return RecoverySignal(
        source=f"monitor_{index}",
        signal_type=RecoverySignalType.WORKER_CRASH.value,
        severity=RecoverySeverity.HIGH.value,
        epoch=index,
        seq_id=0,
        evidence_hashes=(f"hash_{index}",),
    )


def make_diagnosis(index: int) -> RecoveryDiagnosis:
    return RecoveryDiagnosis(
        classification=DiagnosisClassification.ISOLATED_FAILURE.value,
        identified_failures=(f"failure_{index}",),
        root_cause_hypothesis=f"cause_{index}",
        confidence=0.9,
        evidence_count=1,
    )


def make_plan(index: int) -> RecoveryPlan:
    step = RecoveryStep(
        step_type=RecoveryStepType.RUN_REPLAY_VERIFICATION.value,
        target=f"node_{index}",
        reason="read only verification",
        parameters={"index": index},
    )
    return RecoveryPlan(
        steps=(step,),
        estimated_duration_seconds=30,
        rollback_plan_hash=f"rollback_{index}",
    )


def make_proposal(index: int) -> RecoveryProposal:
    return RecoveryProposal(
        signal=make_signal(index),
        diagnosis=make_diagnosis(index),
        plan=make_plan(index),
        reason_for_proposal=f"proposal_{index}",
    )


def make_simulation(proposal: RecoveryProposal, risk: str) -> RecoverySimulationReport:
    return RecoverySimulationReport(
        proposal_hash=proposal.proposal_hash,
        report_hash=None,
        overall_risk=risk,
        ready_for_handoff=risk != RecoverySimulationRiskLevel.BLOCKED.value,
        step_simulations=(),
        warnings=(),
        blocked_reasons=("blocked",) if risk == RecoverySimulationRiskLevel.BLOCKED.value else (),
    )


def make_decision(
    proposal: RecoveryProposal,
    simulation: RecoverySimulationReport,
    decision: str,
    blocked_reason_codes=(),
) -> RecoveryHandoffDecision:
    return RecoveryHandoffDecision(
        decision=decision,
        decision_reason=f"reason_{decision}",
        proposal_hash=proposal.proposal_hash,
        simulation_hash=simulation.simulation_hash,
        authority_name="authority",
        authority_response_hash=stable_hash({
            "authority": "authority",
            "decision": decision,
        }),
        ready_for_execution=decision == RecoveryAuthorityDecision.APPROVED.value,
        blocked_reason_codes=tuple(blocked_reason_codes),
    )


def make_registry_with_full_artifact():
    proposal = make_proposal(1)
    simulation = make_simulation(proposal, RecoverySimulationRiskLevel.LOW.value)
    decision = make_decision(proposal, simulation, RecoveryAuthorityDecision.APPROVED.value)
    registry = (
        RecoveryArtifactRegistry()
        .register_proposal(proposal)
        .register_simulation(simulation)
        .register_handoff(decision)
    )
    return registry, proposal, simulation, decision


def test_same_artifacts_produce_identical_timeline_and_analytics():
    registry, proposal, _, _ = make_registry_with_full_artifact()
    service = RecoveryObservabilityService(registry)
    other_service = RecoveryObservabilityService(
        RecoveryArtifactRegistry(
            proposals=tuple(reversed(registry.proposals)),
            simulations=tuple(reversed(registry.simulations)),
            handoffs=tuple(reversed(registry.handoffs)),
        )
    )

    assert service.get_recovery_timeline(proposal.proposal_hash) == other_service.get_recovery_timeline(proposal.proposal_hash)
    assert service.get_recovery_analytics() == other_service.get_recovery_analytics()


def test_registry_register_methods_are_copy_on_write():
    proposal = make_proposal(1)
    simulation = make_simulation(proposal, RecoverySimulationRiskLevel.LOW.value)
    decision = make_decision(proposal, simulation, RecoveryAuthorityDecision.APPROVED.value)
    empty = RecoveryArtifactRegistry()

    with_proposal = empty.register_proposal(proposal)
    with_simulation = with_proposal.register_simulation(simulation)
    with_decision = with_simulation.register_handoff(decision)

    assert empty.proposals == ()
    assert empty.simulations == ()
    assert empty.handoffs == ()
    assert with_proposal.proposals == (proposal,)
    assert with_simulation.simulations == (simulation,)
    assert with_decision.handoffs == (decision,)


def test_timeline_order_is_fixed():
    registry, proposal, _, _ = make_registry_with_full_artifact()
    timeline = RecoveryObservabilityService(registry).get_recovery_timeline(proposal.proposal_hash)

    assert [event.sequence for event in timeline.events] == [
        SIGNAL_DETECTED,
        CLASSIFIED,
        PLAN_BUILT,
        SIMULATION_COMPLETED,
        AUTHORITY_HANDOFF,
        AUTHORITY_DECISION,
    ]
    assert [event.event_type for event in timeline.events] == [
        EVENT_SIGNAL,
        EVENT_CLASSIFICATION,
        EVENT_PLAN,
        EVENT_SIMULATION,
        EVENT_HANDOFF,
        EVENT_DECISION,
    ]


def test_registry_artifact_lists_are_canonically_sorted():
    proposal_a = make_proposal(1)
    proposal_b = make_proposal(2)
    simulation_a = make_simulation(proposal_a, RecoverySimulationRiskLevel.LOW.value)
    simulation_b = make_simulation(proposal_b, RecoverySimulationRiskLevel.HIGH.value)
    decision_a = make_decision(proposal_a, simulation_a, RecoveryAuthorityDecision.APPROVED.value)
    decision_b = make_decision(proposal_b, simulation_b, RecoveryAuthorityDecision.DEFERRED.value)

    registry = RecoveryArtifactRegistry(
        proposals=(proposal_b, proposal_a),
        simulations=(simulation_b, simulation_a),
        handoffs=(decision_b, decision_a),
    )
    service = RecoveryObservabilityService(registry)

    assert service.list_recovery_proposals() == tuple(sorted((proposal_a.proposal_hash, proposal_b.proposal_hash)))
    assert registry.simulations == tuple(sorted(registry.simulations, key=lambda item: (item.proposal_hash, item.simulation_hash)))
    assert registry.handoffs == tuple(sorted(registry.handoffs, key=lambda item: (
        item.proposal_hash,
        item.simulation_hash,
        item.decision_hash,
    )))


def test_analytics_counts_are_correct():
    approved = make_proposal(1)
    rejected = make_proposal(2)
    deferred = make_proposal(3)
    blocked = make_proposal(4)

    approved_sim = make_simulation(approved, RecoverySimulationRiskLevel.LOW.value)
    rejected_sim = make_simulation(rejected, RecoverySimulationRiskLevel.MEDIUM.value)
    deferred_sim = make_simulation(deferred, RecoverySimulationRiskLevel.HIGH.value)
    blocked_sim = make_simulation(blocked, RecoverySimulationRiskLevel.BLOCKED.value)

    registry = RecoveryArtifactRegistry(
        proposals=(approved, rejected, deferred, blocked),
        simulations=(approved_sim, rejected_sim, deferred_sim, blocked_sim),
        handoffs=(
            make_decision(approved, approved_sim, RecoveryAuthorityDecision.APPROVED.value),
            make_decision(rejected, rejected_sim, RecoveryAuthorityDecision.REJECTED.value),
            make_decision(deferred, deferred_sim, RecoveryAuthorityDecision.DEFERRED.value),
        ),
    )

    snapshot = RecoveryObservabilityService(registry).get_recovery_analytics()

    assert snapshot.total_proposals == 4
    assert snapshot.approved_count == 1
    assert snapshot.rejected_count == 1
    assert snapshot.deferred_count == 1
    assert snapshot.blocked_simulations == 1
    assert snapshot.high_risk_count == 1
    assert snapshot.medium_risk_count == 1
    assert snapshot.low_risk_count == 1


def test_analytics_hash_uses_explicit_payload_order():
    snapshot = RecoveryObservabilityService(RecoveryArtifactRegistry()).get_recovery_analytics()

    assert list(snapshot.to_hash_payload().keys()) == [
        "approved_count",
        "blocked_simulations",
        "deferred_count",
        "high_risk_count",
        "low_risk_count",
        "medium_risk_count",
        "rejected_count",
        "total_proposals",
    ]
    assert snapshot.analytics_hash == stable_hash(snapshot.to_hash_payload())


def test_blocked_recovery_listing_includes_only_blocked_items():
    blocked_sim_proposal = make_proposal(1)
    blocked_decision_proposal = make_proposal(2)
    normal_rejected_proposal = make_proposal(3)

    blocked_simulation = make_simulation(blocked_sim_proposal, RecoverySimulationRiskLevel.BLOCKED.value)
    decision_simulation = make_simulation(blocked_decision_proposal, RecoverySimulationRiskLevel.LOW.value)
    normal_rejected_simulation = make_simulation(normal_rejected_proposal, RecoverySimulationRiskLevel.LOW.value)
    blocked_decision = make_decision(
        blocked_decision_proposal,
        decision_simulation,
        RecoveryAuthorityDecision.REJECTED.value,
        blocked_reason_codes=("BLOCKED_SIMULATION_NOT_READY",),
    )
    normal_rejected = make_decision(
        normal_rejected_proposal,
        normal_rejected_simulation,
        RecoveryAuthorityDecision.REJECTED.value,
    )
    registry = RecoveryArtifactRegistry(
        proposals=(blocked_sim_proposal, blocked_decision_proposal, normal_rejected_proposal),
        simulations=(blocked_simulation, decision_simulation, normal_rejected_simulation),
        handoffs=(blocked_decision, normal_rejected),
    )

    assert RecoveryObservabilityService(registry).list_blocked_recoveries() == tuple(sorted((
        blocked_sim_proposal.proposal_hash,
        blocked_decision_proposal.proposal_hash,
    )))


def test_missing_timeline_and_decision_are_deterministic():
    service = RecoveryObservabilityService(RecoveryArtifactRegistry())
    timeline = service.get_recovery_timeline("missing")

    assert timeline.proposal_hash == "missing"
    assert timeline.events == ()
    assert service.get_recovery_decision("missing") is None


def test_s5_module_passes_ast_safety_scan():
    import src.services.governance.recovery.recovery_observability as module

    source = inspect.getsource(module)
    is_safe, violations = check_recovery_code_safety(source)

    assert is_safe, "\n".join(violations)


def test_safety_gate_rejects_s5_forbidden_fixtures():
    fixtures = [
        "approve_recovery(item)",
        "reject_recovery(item)",
        "retry_recovery(item)",
    ]

    for code in fixtures:
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert violations
