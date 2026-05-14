import re
import sqlite3
from pathlib import Path

import pytest

from src.projections.db_projection_reader import DBProjectionReader


FORBIDDEN_SQL = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE")


def test_missing_database_returns_degraded_fallback(tmp_path: Path):
    result = DBProjectionReader(tmp_path / "missing.db").read_recovery()

    assert result.status == "degraded"
    assert result.source == "deterministic_fallback"
    assert result.items == ()
    assert result.diagnostics["reason"] == "missing_database"
    assert result.metadata["read_only"] is True
    assert result.metadata["source_of_truth"] == "ledger"


def test_empty_database_table_returns_connected_empty_result(tmp_path: Path):
    db_path = tmp_path / "projection.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE recovery_projection (id TEXT PRIMARY KEY, label TEXT)")

    result = DBProjectionReader(db_path).read_recovery()

    assert result.status == "empty"
    assert result.source == "database_projection"
    assert result.items == ()
    assert result.diagnostics == {"connected": True, "degraded": False, "reason": "empty_table"}
    assert result.metadata["table"] == "recovery_projection"


def test_rows_are_sorted_deterministically(tmp_path: Path):
    db_path = tmp_path / "projection.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE mesh_projection (id TEXT PRIMARY KEY, stable_order INTEGER, label TEXT)")
        conn.executemany(
            "INSERT INTO mesh_projection (id, stable_order, label) VALUES (?, ?, ?)",
            [("mesh-b", 20, "B"), ("mesh-a", 10, "A")],
        )

    first = DBProjectionReader(db_path).read_mesh()
    second = DBProjectionReader(db_path).read_mesh()

    assert [item["id"] for item in first.items] == ["mesh-a", "mesh-b"]
    assert first == second


def test_reader_opens_database_read_only(tmp_path: Path):
    db_path = tmp_path / "projection.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE policy_projection (id TEXT PRIMARY KEY)")

    reader = DBProjectionReader(db_path)
    with reader._connect() as conn:  # noqa: SLF001
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE should_not_exist (id TEXT)")


def test_query_error_returns_truthful_degraded_fallback(tmp_path: Path):
    db_path = tmp_path / "projection.db"
    db_path.write_text("not sqlite", encoding="utf-8")

    result = DBProjectionReader(db_path).read_replay()

    assert result.status == "degraded"
    assert result.source == "deterministic_fallback"
    assert result.diagnostics["reason"] == "query_error"
    assert result.diagnostics["detail"] in {"DatabaseError", "OperationalError"}


def test_reader_source_contains_no_mutation_sql_or_forbidden_imports():
    source = Path("src/projections/db_projection_reader.py").read_text(encoding="utf-8")
    for keyword in FORBIDDEN_SQL:
        assert re.search(rf"\b{keyword}\b", source.upper()) is None

    lowered = source.lower()
    forbidden_imports = (
        "meshorchestrator",
        "control_ops",
        "executor",
        "repair_engine",
        "promotion",
        "write_ledger",
    )
    for token in forbidden_imports:
        assert token not in lowered
