from dataclasses import FrozenInstanceError
import pytest

from src.services.governance.policy_graph import (
    PolicyDiffEngine,
    PolicyGraphEngine,
    PolicySnapshot,
    PromotionPipeline,
    RollbackManager,
)


def snapshot(rate=0.07, threshold=1000, role="finance"):
    return PolicySnapshot(
        rules={"tax": {"rate": rate}},
        thresholds={"approval": threshold},
        permissions={"approve": [role]},
        governance_constraints={"quorum_required": True},
    )


def test_policy_snapshot_and_version_are_immutable():
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(), [], "admin", "base")

    with pytest.raises(TypeError):
        version.snapshot.rules["tax"] = {"rate": 0.10}
    with pytest.raises(FrozenInstanceError):
        version.stage = "production"


def test_version_ids_are_deterministic_from_ledger_metadata():
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(), [], "admin", "base")

    rebuilt = PolicyGraphEngine.rebuild_from_ledger(graph.transition_events)
    rebuilt_version = rebuilt.current_head()

    assert rebuilt_version.version_id == version.version_id
    assert rebuilt_version.snapshot.snapshot_hash == version.snapshot.snapshot_hash


def test_linear_and_branched_lineage_projection():
    graph = PolicyGraphEngine()
    v17 = graph.create_version(snapshot(rate=0.07), [], "admin", "v17")
    v18 = graph.create_version(snapshot(rate=0.08), [v17.version_id], "admin", "v18")
    v19_experiment = graph.create_version(snapshot(rate=0.09), [v18.version_id], "admin", "experiment")
    v19_production = graph.create_version(snapshot(rate=0.10), [v18.version_id], "admin", "production")

    assert [v.version_id for v in graph.lineage_of(v19_experiment.version_id)] == [
        v17.version_id,
        v18.version_id,
        v19_experiment.version_id,
    ]
    assert [v.version_id for v in graph.children_of(v18.version_id)] == sorted([
        v19_experiment.version_id,
        v19_production.version_id,
    ])


def test_policy_diff_is_canonical_and_sorted():
    graph = PolicyGraphEngine()
    v1 = graph.create_version(snapshot(rate=0.07, threshold=1000, role="finance"), [], "admin", "base")
    v2 = graph.create_version(snapshot(rate=0.10, threshold=500, role="director"), [v1.version_id], "admin", "change")

    diff = PolicyDiffEngine(graph).diff(v1.version_id, v2.version_id)

    assert [(c.section, c.path, c.operation) for c in diff.changes] == sorted(
        (c.section, c.path, c.operation) for c in diff.changes
    )
    assert ("rules", "tax.rate", "changed") in [(c.section, c.path, c.operation) for c in diff.changes]
    assert ("thresholds", "approval", "changed") in [(c.section, c.path, c.operation) for c in diff.changes]
    assert ("permissions", "approve", "changed") in [(c.section, c.path, c.operation) for c in diff.changes]


def test_rollback_creates_new_version_without_mutating_target():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(rate=0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(rate=0.10), [base.version_id], "admin", "changed")
    original_base_stage = base.stage

    rollback = RollbackManager(graph).rollback_to(base.version_id, "admin", "restore base")

    assert rollback.version_id != base.version_id
    assert rollback.rollback_target_id == base.version_id
    assert rollback.snapshot.snapshot_hash == base.snapshot.snapshot_hash
    assert rollback.parent_version_ids == (changed.version_id,)
    assert base.stage == original_base_stage
    assert graph.get_version(base.version_id).stage == original_base_stage


def test_rebuild_from_committed_ledger_events_skips_uncommitted_payloads():
    graph = PolicyGraphEngine()
    committed = graph.create_version(snapshot(rate=0.07), [], "admin", "committed")
    uncommitted_event = graph.transition_events[-1]
    uncommitted_event = type(uncommitted_event)(
        **{**uncommitted_event.__dict__, "payload": {**uncommitted_event.payload, "committed": False}}
    )

    rebuilt = PolicyGraphEngine.rebuild_from_ledger([*graph.transition_events, uncommitted_event])

    assert rebuilt.get_version(committed.version_id).version_id == committed.version_id
    assert len(rebuilt.versions) == 1


def test_reconstruct_at_uses_ledger_timestamps_only():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(rate=0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(rate=0.10), [base.version_id], "admin", "changed")

    reconstructed = graph.reconstruct_at(base.ledger_timestamp)

    assert reconstructed.snapshot_hash == base.snapshot.snapshot_hash
    assert reconstructed.snapshot_hash != changed.snapshot.snapshot_hash


def test_successful_quorum_promotion_uses_mesh_orchestrator():
    graph = PolicyGraphEngine()
    pipeline = PromotionPipeline(graph)
    version = graph.create_version(snapshot(), [], "admin", "base")

    simulation = pipeline.promote(version.version_id, "simulation", "admin")
    approved = pipeline.promote(simulation.version_id, "approved", "admin", ["n1", "n2"])
    production = pipeline.promote(approved.version_id, "production", "admin", ["n1", "n2"])

    assert production.stage == "production"
    assert graph.get_production_head().version_id == version.version_id
    assert len(graph.mesh_orchestrator.leader.event_log) == 4


def test_failed_quorum_promotion_does_not_append_success_event():
    graph = PolicyGraphEngine()
    pipeline = PromotionPipeline(graph)
    version = graph.create_version(snapshot(), [], "admin", "base")
    simulation = pipeline.promote(version.version_id, "simulation", "admin")
    event_count = len(graph.mesh_orchestrator.leader.event_log)

    with pytest.raises(Exception, match="Quorum not reached"):
        pipeline.promote(simulation.version_id, "approved", "admin", ["n1"])

    assert len(graph.mesh_orchestrator.leader.event_log) == event_count
    assert graph.get_version(simulation.version_id).stage == "simulation"


def test_no_direct_production_promotion():
    graph = PolicyGraphEngine()
    pipeline = PromotionPipeline(graph)
    version = graph.create_version(snapshot(), [], "admin", "base")

    with pytest.raises(ValueError, match="Invalid promotion transition"):
        pipeline.promote(version.version_id, "production", "admin", ["n1", "n2"])
