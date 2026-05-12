import sqlite3
import threading
import json
import pytest

from src.services.governance.policy_graph import (
    IncrementalRepair,
    IndexIntegrityChecker,
    PolicyGraphEngine,
    PolicySnapshot,
    RestartRebuilder,
    SQLitePolicyGraphStore,
)
from src.services.governance.policy_graph.policy_version import canonical_json


def snapshot(rate=0.07):
    return PolicySnapshot(
        rules={"tax": {"rate": rate}},
        thresholds={"approval": 1000},
        permissions={"approve": ["finance"]},
        governance_constraints={"quorum_required": True},
    )


def build_graph():
    graph = PolicyGraphEngine()
    base = graph.create_version(snapshot(0.07), [], "admin", "base")
    changed = graph.create_version(snapshot(0.10), [base.version_id], "admin", "changed")
    return graph, base, changed


def test_schema_migration_bootstrap(tmp_path):
    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"))

    assert store.load_schema_version() == 1
    with sqlite3.connect(tmp_path / "policy_graph.db") as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    assert "schema_version" in tables
    assert "policy_versions" in tables
    assert mode.lower() == "wal"


def test_schema_version_gate_refuses_incompatible_schema(tmp_path):
    db_path = tmp_path / "policy_graph.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE schema_version (component TEXT PRIMARY KEY, version INTEGER NOT NULL)")
        conn.execute(
            "INSERT INTO schema_version (component, version) VALUES (?, ?)",
            ("policy_graph", 999),
        )

    with pytest.raises(RuntimeError, match="newer than this runtime"):
        SQLitePolicyGraphStore(str(db_path))


def test_incremental_repair_corrects_missing_version_row(tmp_path):
    graph, base, changed = build_graph()
    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    with sqlite3.connect(tmp_path / "policy_graph.db") as conn:
        conn.execute("DELETE FROM policy_versions WHERE version_id = ?", (changed.version_id,))

    result = IncrementalRepair(store).repair(graph.transition_events)

    assert result.repaired is True
    assert result.mode == "INCREMENTAL_REPAIR"
    assert result.reason == "MISSING_VERSION"
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_duplicate_orphan_and_self_cycle_corruption_detection(tmp_path):
    graph, base, changed = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    base_row = next(row for row in store.load_versions() if row["version_id"] == base.version_id)

    with sqlite3.connect(db_path) as conn:
        columns = [
            "version_id", "snapshot_hash", "stage", "actor", "reason", "rollback_target_id",
            "ledger_event_id", "ledger_global_hash", "ledger_seq_id", "ledger_timestamp", "snapshot_json"
        ]
        conn.execute(
            f"INSERT INTO policy_versions ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            tuple(base_row[column] for column in columns),
        )

    assert IndexIntegrityChecker(store).verify(graph.transition_events).reason == "DUPLICATE_VERSION_ID"

    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO policy_parent_edges (parent_version_id, child_version_id) VALUES (?, ?)",
            (base.version_id, changed.version_id),
        )

    assert IndexIntegrityChecker(store).verify(graph.transition_events).reason == "DUPLICATE_PARENT_EDGE"

    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO policy_parent_edges (parent_version_id, child_version_id) VALUES (?, ?)",
            (base.version_id, base.version_id),
        )

    assert IndexIntegrityChecker(store).verify(graph.transition_events).reason == "SELF_CYCLE_EDGE"

    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO policy_parent_edges (parent_version_id, child_version_id) VALUES (?, ?)",
            ("missing-parent", changed.version_id),
        )

    assert IndexIntegrityChecker(store).verify(graph.transition_events).reason == "ORPHAN_PARENT_EDGE"


def test_snapshot_hash_recompute_detection_and_repair(tmp_path):
    graph, base, changed = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    row = next(row for row in store.load_versions() if row["version_id"] == base.version_id)
    snapshot_payload = {
        **json.loads(row["snapshot_json"]),
        "rules": {"tax": {"rate": 0.99}},
    }

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE policy_versions SET snapshot_json = ? WHERE version_id = ?",
            (canonical_json(snapshot_payload), base.version_id),
        )

    assert IndexIntegrityChecker(store).verify(graph.transition_events).reason == "SNAPSHOT_HASH_RECOMPUTE_MISMATCH"
    repair = IncrementalRepair(store).repair(graph.transition_events)
    assert repair.mode == "INCREMENTAL_REPAIR"
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_fallback_full_rebuild_on_timestamp_order_corruption(tmp_path):
    graph, base, changed = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE policy_versions SET ledger_timestamp = ? WHERE version_id = ?",
            ("9999999999", base.version_id),
        )

    result = IncrementalRepair(store).repair(graph.transition_events)

    assert result.mode == "FULL_REBUILD"
    assert result.reason == "TIMESTAMP_ORDER_CORRUPTION"
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_interrupted_write_recovery_ledger_wins(tmp_path):
    graph, base, changed = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    conn = store.lock_manager.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM policy_versions WHERE version_id = ?", (changed.version_id,))
        conn.rollback()
    finally:
        conn.close()

    loaded = RestartRebuilder(store).rebuild_or_verify(graph.transition_events)

    assert loaded.get_version(changed.version_id).version_id == changed.version_id
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_partial_committed_write_recovery_ledger_wins(tmp_path):
    graph, base, changed = build_graph()
    db_path = tmp_path / "policy_graph.db"
    store = SQLitePolicyGraphStore(str(db_path))
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)

    with store.lock_manager.write_transaction() as conn:
        conn.execute("DELETE FROM policy_parent_edges WHERE child_version_id = ?", (changed.version_id,))
        conn.execute("DELETE FROM policy_versions WHERE version_id = ?", (changed.version_id,))

    result = IncrementalRepair(store).repair(graph.transition_events)

    assert result.mode == "INCREMENTAL_REPAIR"
    assert result.reason == "MISSING_VERSION"
    assert store.load_versions()
    assert IndexIntegrityChecker(store).verify(graph.transition_events).ok is True


def test_concurrent_reader_writer_safety(tmp_path):
    graph, base, changed = build_graph()
    store = SQLitePolicyGraphStore(str(tmp_path / "policy_graph.db"), busy_timeout_ms=5000)
    RestartRebuilder(store).rebuild_index_from_ledger(graph.transition_events)
    errors = []
    observations = []

    def reader():
        try:
            for _ in range(20):
                observations.append(len(store.load_versions()))
        except Exception as exc:
            errors.append(exc)

    def writer():
        try:
            for _ in range(5):
                RestartRebuilder(store).rebuild_or_verify(graph.transition_events)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=reader), threading.Thread(target=writer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert observations
    assert all(count == 2 for count in observations)
