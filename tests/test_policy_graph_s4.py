from dataclasses import FrozenInstanceError
import pytest

from src.services.governance.policy_graph import (
    AuditQueryEngine,
    GovernanceExplanation,
    LineageExplainer,
    PolicyGraphEngine,
    PolicySnapshot,
    PromotionPipeline,
    RollbackManager,
)
from src.services.governance.policy_graph.policy_version import POLICY_VERSION_ROLLBACK


def snapshot(rate=0.07, threshold=1000, role="finance"):
    return PolicySnapshot(
        rules={"tax": {"rate": rate}},
        thresholds={"approval": threshold},
        permissions={"approve": [role]},
        governance_constraints={"quorum_required": True},
    )


def promoted_graph():
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(0.07), [], "admin", "base")
    pipeline = PromotionPipeline(graph)
    simulation = pipeline.promote(version.version_id, "simulation", "admin")
    approved = pipeline.promote(simulation.version_id, "approved", "admin", ["n1", "n2"])
    production = pipeline.promote(approved.version_id, "production", "admin", ["n1", "n2"])
    return graph, version, production


def test_timestamp_reconstruction_from_committed_ledger_only():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    query = AuditQueryEngine(graph_engine=graph)

    before_change = query.policy_at_timestamp(base.ledger_timestamp)

    assert before_change.snapshot_hash == base.snapshot.snapshot_hash
    assert before_change.snapshot_hash != changed.snapshot.snapshot_hash


def test_timestamp_ties_use_canonical_ledger_ordering():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    tied_events = [
        type(event)(**{**event.__dict__, "timestamp": "2026-01-01T00:00:00+00:00"})
        for event in graph.transition_events
    ]

    reconstructed = AuditQueryEngine(events=list(reversed(tied_events))).policy_at_timestamp("2026-01-01T00:00:00+00:00")

    assert reconstructed.snapshot_hash == changed.snapshot.snapshot_hash


def test_policy_reconstruction_by_version_id_and_cached_graph_replay_truth():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    graph.versions[changed.version_id] = graph.versions[base.version_id]

    query = AuditQueryEngine(graph_engine=graph)

    assert query.policy_at_version(changed.version_id).snapshot_hash == changed.snapshot.snapshot_hash


def test_lineage_and_descendant_traversal():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    branch = graph.create_version(snapshot(0.11), [base.version_id], "admin", "branch")
    lineage = LineageExplainer(graph_engine=graph)

    assert [v.version_id for v in lineage.ancestors(changed.version_id)] == [base.version_id]
    assert [v.version_id for v in lineage.descendants(base.version_id)] == [changed.version_id, branch.version_id]


def test_rollback_ancestry_and_impact_diff():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    rollback = RollbackManager(graph).rollback_to(base.version_id, "admin", "restore")
    query = AuditQueryEngine(graph_engine=graph)

    assert [v.version_id for v in query.rollback_ancestry(rollback.version_id)] == [base.version_id]
    diff = query.rollback_impact_diff(rollback.version_id)
    assert diff.from_version_id == changed.version_id
    assert diff.to_version_id == rollback.version_id
    assert ("rules", "tax.rate", "changed") in [(c.section, c.path, c.operation) for c in diff.changes]


def test_rollback_ancestry_cycle_detection():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    rollback = RollbackManager(graph).rollback_to(base.version_id, "admin", "restore")
    lineage = LineageExplainer(graph_engine=graph)
    lineage.graph.versions[base.version_id] = type(base)(
        **{**base.__dict__, "rollback_target_id": rollback.version_id}
    )

    with pytest.raises(ValueError, match="Rollback ancestry cycle detected"):
        lineage.rollback_ancestry(rollback.version_id)


def test_promotion_lineage_and_quorum_explanation():
    graph, version, production = promoted_graph()
    query = AuditQueryEngine(graph_engine=graph)

    lineage = query.promotion_lineage(version.version_id)
    explanation = query.explain_version(version.version_id)

    assert [item.to_stage for item in lineage] == ["simulation", "approved", "production"]
    assert explanation.approvals == ("n1", "n2")
    assert explanation.quorum_proofs == ("n1", "n2")
    assert "simulation->approved" in explanation.transitions
    assert "approved->production" in explanation.transitions
    assert production.stage == "production"


def test_diff_queries_and_production_only_diff():
    graph = PolicyGraphEngine()
    v1 = graph.create_version(snapshot(0.07), [], "admin", "base")
    v2 = graph.create_version(snapshot(0.10), [v1.version_id], "admin", "changed")
    pipeline = PromotionPipeline(graph)
    for version in (v1, v2):
        simulation = pipeline.promote(version.version_id, "simulation", "admin")
        approved = pipeline.promote(simulation.version_id, "approved", "admin", ["n1", "n2"])
        pipeline.promote(approved.version_id, "production", "admin", ["n1", "n2"])
    query = AuditQueryEngine(graph_engine=graph)

    diff = query.diff_versions(v1.version_id, v2.version_id)
    production_diff = query.production_diff(v1.version_id, v2.version_id)

    assert diff.changes == production_diff.changes
    assert ("rules", "tax.rate", "changed") in [(c.section, c.path, c.operation) for c in diff.changes]


def test_absent_evidence_returns_empty_fields_without_inference():
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(), [], "", "")
    event = graph.transition_events[-1]
    graph.transition_events[-1] = type(event)(**{**event.__dict__, "actor": "", "payload": {**event.payload, "actor": "", "reason": ""}})
    explanation = AuditQueryEngine(graph_engine=graph).explain_version(version.version_id)

    assert explanation.actors == ()
    assert explanation.approvals == ()
    assert explanation.reasons == ()
    assert explanation.quorum_proofs == ()


def test_governance_explanation_is_frozen_and_hash_is_deterministic():
    graph, version, production = promoted_graph()
    first = AuditQueryEngine(graph_engine=graph).explain_version(version.version_id)
    second = AuditQueryEngine(events=list(reversed(graph.transition_events))).explain_version(version.version_id)

    assert isinstance(first, GovernanceExplanation)
    assert first.explanation_hash == second.explanation_hash
    assert first.to_payload() == second.to_payload()
    with pytest.raises(FrozenInstanceError):
        first.version_id = "changed"
