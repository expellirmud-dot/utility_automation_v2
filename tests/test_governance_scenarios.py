from dataclasses import FrozenInstanceError

import pytest

from src.services.governance.policy_graph import PolicyGraphEngine, PolicySnapshot
from src.services.governance.simulation import GovernanceSimulationEngine, SimulationScenarioEngine


def _snapshot(rate=0.07, approval=1000, emergency=100, permissions=None, constraints=None, rules=None):
    return PolicySnapshot(
        rules=rules or {"tax": {"rate": rate}},
        thresholds={"approval": approval, "emergency": emergency},
        permissions=permissions or {"approve": ["finance"], "promote": ["governance"]},
        governance_constraints=constraints or {"quorum_required": True, "multi_sig_required": True},
    )


def _build_engine():
    graph = PolicyGraphEngine()
    version = graph.create_version(_snapshot(), [], "admin", "base")
    sim = GovernanceSimulationEngine(graph_engine=graph)
    return graph, version, SimulationScenarioEngine(sim)


def test_deterministic_batch_hashes_and_no_side_effects():
    graph, version, engine = _build_engine()
    before_events = tuple(event.global_chain_hash for event in graph.transition_events)
    before_versions = tuple(sorted(graph.versions.keys()))

    c1 = _snapshot(approval=500)
    c2 = _snapshot(approval=500, rules={"tax": {"rate": 0.08}})
    a = engine.simulate_scenarios([c1, c2], version.version_id, "analyst", "batch-a")
    b = engine.simulate_scenarios([c2, c1], version.version_id, "analyst", "batch-a")

    assert a.batch_hash == b.batch_hash
    assert [c.scenario_hash for c in a.scenario_reports] == [c.scenario_hash for c in b.scenario_reports]
    assert tuple(event.global_chain_hash for event in graph.transition_events) == before_events
    assert tuple(sorted(graph.versions.keys())) == before_versions


def test_stable_ranking_precedence_and_tiebreak():
    _, version, engine = _build_engine()
    allow = _snapshot()
    quorum = _snapshot(constraints={"quorum_required": True, "multi_sig_required": True}, approval=1000)
    manual = _snapshot(approval=500)
    blocker = _snapshot(
        approval=500,
        permissions={"approve": ["finance"], "promote": ["finance"]},
        constraints={"quorum_required": False, "multi_sig_required": False},
        rules={"a": {"depends_on": ["missing_rule"]}},
    )

    report = engine.simulate_scenarios([allow, quorum, manual, blocker], version.version_id, "analyst", "rank")
    recs = [item.recommendation for item in report.candidate_comparisons]
    assert recs[0] == "block_until_fixed"
    assert recs[-1] in {"allow_simulation", "quorum_required"}
    assert report.candidate_comparisons == tuple(sorted(report.candidate_comparisons, key=lambda c: c.rank_key))


def test_cascading_conflict_detection_and_immutability():
    _, version, engine = _build_engine()
    candidate = _snapshot(
        approval=400,
        emergency=800,
        permissions={"approve": ["ops"], "promote": ["ops"]},
        constraints={"quorum_required": False, "multi_sig_required": False},
        rules={"r1": {"depends_on": ["r2"]}},
    )
    batch = engine.simulate_scenarios([candidate], version.version_id, "analyst", "cascade")
    conflict_types = {c.conflict_type for c in batch.scenario_reports[0].simulation_report.conflict_findings}
    assert "THRESHOLD_INTERACTION_FAILURE" in conflict_types
    assert "PERMISSION_ESCALATION_CASCADE" in conflict_types
    assert "GOVERNANCE_CONSTRAINT_WEAKENING_CHAIN" in conflict_types
    assert "RULE_DEPENDENCY_CONFLICT" in conflict_types

    with pytest.raises(FrozenInstanceError):
        batch.batch_hash = "mutate"


def test_no_authority_mutation_or_quorum_paths_present():
    from pathlib import Path

    package_sources = "\n".join(path.read_text() for path in Path("src/services/governance/simulation").glob("*.py"))

    assert "promote(" not in package_sources
    assert "submit_critical_event" not in package_sources
    assert "propose_event" not in package_sources
    assert "MeshOrchestrator" not in package_sources
    assert "sqlite" not in package_sources.lower()
