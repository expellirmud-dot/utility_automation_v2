from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.services.governance.policy_graph import PolicyGraphEngine, PolicySnapshot, PromotionPipeline
from src.services.governance.simulation import AIAdvice, EvidenceOnlyAIAdvisor, GovernanceSimulationEngine


def snapshot(rate=0.07, threshold=1000, role="finance", quorum_required=True, rules=None):
    return PolicySnapshot(
        rules=rules or {"tax": {"rate": rate}},
        thresholds={"approval": threshold},
        permissions={"approve": [role]},
        governance_constraints={"quorum_required": quorum_required},
    )


class ChangingAdvisor:
    def __init__(self, warning):
        self.warning = warning

    def advise(self, deterministic_evidence):
        return AIAdvice(warnings=(self.warning,), notes=("different non-deterministic wording",))


def build_graph():
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(), [], "admin", "base")
    return graph, version


def test_simulation_is_pure_and_does_not_mutate_graph_or_ledger():
    graph, version = build_graph()
    original_events = tuple(event.global_chain_hash for event in graph.transition_events)
    original_versions = tuple(sorted((item.version_id, item.stage) for item in graph.versions.values()))

    report = GovernanceSimulationEngine(graph_engine=graph).simulate_policy_change(
        snapshot(rate=0.10, threshold=750),
        base_version_id=version.version_id,
    )

    assert tuple(event.global_chain_hash for event in graph.transition_events) == original_events
    assert tuple(sorted((item.version_id, item.stage) for item in graph.versions.values())) == original_versions
    assert report.base_version_id == version.version_id
    assert graph.current_head().version_id == version.version_id


def test_candidate_snapshot_and_simulation_hash_are_deterministic():
    graph, version = build_graph()
    candidate_a = PolicySnapshot(
        permissions={"approve": ["director"]},
        thresholds={"approval": 500},
        governance_constraints={"quorum_required": True},
        rules={"tax": {"rate": 0.10}},
    )
    candidate_b = PolicySnapshot(
        rules={"tax": {"rate": 0.10}},
        governance_constraints={"quorum_required": True},
        thresholds={"approval": 500},
        permissions={"approve": ["director"]},
    )

    engine = GovernanceSimulationEngine(events=list(reversed(graph.transition_events)))
    first = engine.simulate_policy_change(candidate_a, base_version_id=version.version_id)
    second = engine.simulate_policy_change(candidate_b, base_version_id=version.version_id)

    assert first.candidate_snapshot_hash == second.candidate_snapshot_hash
    assert first.simulation_hash == second.simulation_hash
    assert first.to_payload(include_ai=False) == second.to_payload(include_ai=False)


def test_ai_advice_is_excluded_from_simulation_hash():
    graph, version = build_graph()
    candidate = snapshot(threshold=500)
    first = GovernanceSimulationEngine(graph_engine=graph, ai_advisor=ChangingAdvisor("first")).simulate_policy_change(
        candidate,
        base_version_id=version.version_id,
    )
    second = GovernanceSimulationEngine(graph_engine=graph, ai_advisor=ChangingAdvisor("second")).simulate_policy_change(
        candidate,
        base_version_id=version.version_id,
    )

    assert first.ai_advice != second.ai_advice
    assert first.simulation_hash == second.simulation_hash
    assert first.to_payload(include_ai=False) == second.to_payload(include_ai=False)


def test_recommendation_precedence_is_deterministic():
    graph, version = build_graph()
    simulated = PromotionPipeline(graph).promote(version.version_id, "simulation", "admin")
    engine = GovernanceSimulationEngine(graph_engine=graph)

    quorum_only = engine.preflight_promotion(simulated.version_id, "approved")
    manual = engine.simulate_policy_change(snapshot(threshold=500), base_version_id=version.version_id)
    conflict = engine.simulate_policy_change(
        snapshot(rules={
            "b": {"type": "APPROVAL_LIMIT", "value": 100},
            "a": {"type": "APPROVAL_LIMIT", "value": 200},
        }),
        base_version_id=version.version_id,
    )
    invalid = engine.preflight_promotion(version.version_id, "production")

    assert quorum_only.recommendation == "quorum_required"
    assert manual.recommendation == "manual_review"
    assert conflict.recommendation == "block_until_fixed"
    assert invalid.recommendation == "block_until_fixed"


def test_risk_and_conflict_findings_are_sorted_and_detect_expected_risks():
    graph, version = build_graph()
    report = GovernanceSimulationEngine(graph_engine=graph).simulate_policy_change(
        snapshot(
            threshold=500,
            role="director",
            quorum_required=False,
            rules={
                "z": {"type": "APPROVAL_LIMIT", "value": 1000},
                "a": {"type": "APPROVAL_LIMIT", "value": 500},
            },
        ),
        base_version_id=version.version_id,
    )

    risk_keys = [(item.section, item.path, item.code, item.severity) for item in report.risk_findings]
    conflict_keys = [(item.conflict_type, item.rule_a, item.rule_b) for item in report.conflict_findings]

    assert risk_keys == sorted(risk_keys)
    assert conflict_keys == sorted(conflict_keys)
    assert ("thresholds", "approval", "RISKY_THRESHOLD_CHANGE", "HIGH") in risk_keys
    assert ("governance_constraints", "quorum_required", "GOVERNANCE_CONSTRAINT_WEAKENED", "BLOCKER") in risk_keys
    assert conflict_keys == [("CONFLICT_LIMIT", "a", "z")]
    assert report.recommendation == "block_until_fixed"


def test_preflight_promotion_never_promotes():
    graph, version = build_graph()
    pipeline = PromotionPipeline(graph)
    simulated = pipeline.promote(version.version_id, "simulation", "admin")
    before_stage = graph.get_version(simulated.version_id).stage
    before_events = len(graph.transition_events)

    report = GovernanceSimulationEngine(graph_engine=graph).preflight_promotion(simulated.version_id, "approved")

    assert report.recommendation == "quorum_required"
    assert graph.get_version(simulated.version_id).stage == before_stage
    assert len(graph.transition_events) == before_events


def test_ai_advisory_package_is_isolated_from_authority_paths():
    advisory_source = Path("src/services/governance/simulation/ai_advisor.py").read_text()
    package_sources = "\n".join(
        path.read_text()
        for path in Path("src/services/governance/simulation").glob("*.py")
    )

    assert "MeshOrchestrator" not in advisory_source
    assert "PromotionPipeline" not in advisory_source
    assert "submit_critical_event" not in advisory_source
    assert "propose_event" not in advisory_source
    assert "execute_prompt" not in package_sources
    assert "GeminiClient" not in package_sources


def test_immutable_report_and_test_local_advisor():
    graph, version = build_graph()
    report = GovernanceSimulationEngine(
        graph_engine=graph,
        ai_advisor=EvidenceOnlyAIAdvisor(),
    ).simulate_policy_change(snapshot(threshold=500), base_version_id=version.version_id)

    assert report.ai_advice is not None
    with pytest.raises(FrozenInstanceError):
        report.recommendation = "allow_simulation"
