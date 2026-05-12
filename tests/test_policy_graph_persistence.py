import sqlite3

from src.services.governance.policy_graph import (
    IndexIntegrityChecker,
    PolicyGraphEngine,
    PolicySnapshot,
    PromotionPipeline,
    RestartRebuilder,
    RollbackManager,
    SQLitePolicyGraphStore,
)


def snapshot(rate=0.07, threshold=1000):
    return PolicySnapshot(
        rules={"tax": {"rate": rate}},
        thresholds={"approval": threshold},
        permissions={"approve": ["finance"]},
        governance_constraints={"quorum_required": True},
    )


def build_graph():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(rate=0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(rate=0.10), [base.version_id], "admin", "changed")
    rollback = RollbackManager(graph).rollback_to(base.version_id, "admin", "restore")
    simulation = PromotionPipeline(graph).promote(rollback.version_id, "simulation", "admin")
    return graph, base, changed, simulation


def test_rebuild_index_from_ledger(tmp_path):
    graph, base, changed, simulation = build_graph()
    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"))

    rebuilt = RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    assert rebuilt.current_head().version_id == simulation.version_id
    assert sorted(row["version_id"] for row in store.load_versions()) == sorted(
        [base.version_id, changed.version_id, simulation.version_id]
    )
    assert [event.global_chain_hash for event in store.load_events()] == [
        event.global_chain_hash for event in graph.transition_events
    ]


def test_restart_durability_loads_graph_from_index(tmp_path):
    graph, base, changed, simulation = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    restarted_store = SQLitePolicyGraphStore(str(db_path))
    loaded = RestartRebuilder(restarted_store).load_graph_from_index()

    assert loaded.current_head().version_id == simulation.version_id
    assert loaded.get_version(base.version_id).snapshot.snapshot_hash == base.snapshot.snapshot_hash


def test_corrupted_index_detection(tmp_path):
    graph, base, changed, simulation = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE policy_versions SET snapshot_hash = ? WHERE version_id = ?",
            ("CORRUPTED", base.version_id),
        )

    result = IndexIntegrityChecker(store).verify(graph.transition_events)

    assert result.ok is False
    assert result.reason == "SNAPSHOT_HASH_RECOMPUTE_MISMATCH"


def test_ledger_wins_reconciliation_corrects_corrupted_index(tmp_path):
    graph, base, changed, simulation = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    rebuilder = RestartRebuilder(store)
    rebuilder.rebuild_index_from_ledger(graph.transition_events)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE policy_versions SET stage = ? WHERE version_id = ?",
            ("production", base.version_id),
        )

    reconciled = rebuilder.rebuild_or_verify(graph.transition_events)

    assert reconciled.get_version(base.version_id).stage == base.stage
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_historical_versions_are_not_mutated_in_index(tmp_path):
    graph = PolicyGraphEngine()
    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"))
    base = graph.create_version(snapshot(rate=0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(rate=0.10), [base.version_id], "admin", "changed")
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    before = store.load_versions()

    rollback = RollbackManager(graph).rollback_to(base.version_id, "admin", "restore")
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    after = store.load_versions()

    before_by_id = {row["version_id"]: row for row in before}
    after_by_id = {row["version_id"]: row for row in after}
    assert {k: v for k, v in after_by_id[base.version_id].items() if k != "row_id"} == {
        k: v for k, v in before_by_id[base.version_id].items() if k != "row_id"
    }
    assert {k: v for k, v in after_by_id[changed.version_id].items() if k != "row_id"} == {
        k: v for k, v in before_by_id[changed.version_id].items() if k != "row_id"
    }
    assert rollback.version_id in after_by_id


def test_graph_can_reload_after_quorum_promotion(tmp_path):
    graph = PolicyGraphEngine()
    version = graph.create_version(snapshot(), [], "admin", "base")
    pipeline = PromotionPipeline(graph)
    simulation = pipeline.promote(version.version_id, "simulation", "admin")
    approved = pipeline.promote(simulation.version_id, "approved", "admin", ["n1", "n2"])
    production = pipeline.promote(approved.version_id, "production", "admin", ["n1", "n2"])

    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"))
    rebuilder = RestartRebuilder(store)
    rebuilder.rebuild_index_from_ledger(graph.transition_events)
    loaded = rebuilder.load_graph_from_index()

    assert loaded.get_production_head().version_id == production.version_id
    assert loaded.get_version(version.version_id).stage == "production"
