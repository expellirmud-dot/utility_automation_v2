import json
import sqlite3
from pathlib import Path

from src.services.ops_console.db_projection_reader import OpsProjectionReader


def create_projection_table(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE dashboard_projection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bucket TEXT NOT NULL,
                stable_key TEXT NOT NULL,
                record_type TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bucket, record_type, stable_key)
            )
            """
        )


def insert_projection_record(
    db_path: Path,
    bucket: str,
    stable_key: str,
    record_type: str,
    sort_order: int,
    payload_json: str,
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO dashboard_projection_records
                (bucket, stable_key, record_type, sort_order, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (bucket, stable_key, record_type, sort_order, payload_json),
        )


def test_missing_database_returns_degraded_without_creating_file(tmp_path):
    db_path = tmp_path / "missing.db"
    result = OpsProjectionReader(str(db_path)).read_recovery()

    assert result["status"] == "degraded"
    assert result["diagnostics"]["reason"] == "database_missing"
    assert result["items"] == []
    assert db_path.exists() is False


def test_empty_database_returns_connected_empty_result(tmp_path):
    db_path = tmp_path / "empty.db"
    create_projection_table(db_path)

    result = OpsProjectionReader(str(db_path)).read_mesh()

    assert result["status"] == "connected"
    assert result["degraded"] is False
    assert result["item_count"] == 0
    assert result["items"] == []


def test_rows_are_sorted_deterministically(tmp_path):
    db_path = tmp_path / "records.db"
    create_projection_table(db_path)
    insert_projection_record(db_path, "ops_policy", "z-key", "summary", 2, json.dumps({"summary": "third"}))
    insert_projection_record(db_path, "ops_policy", "a-key", "summary", 2, json.dumps({"summary": "second"}))
    insert_projection_record(db_path, "ops_policy", "m-key", "detail", 1, json.dumps({"summary": "first"}))

    result = OpsProjectionReader(str(db_path)).read_policy()

    assert [item["stable_key"] for item in result["items"]] == ["m-key", "a-key", "z-key"]
    assert [item["payload"]["summary"] for item in result["items"]] == ["first", "second", "third"]


def test_malformed_json_returns_truthful_degraded_diagnostics(tmp_path):
    db_path = tmp_path / "malformed.db"
    create_projection_table(db_path)
    insert_projection_record(db_path, "ops_replay", "bad-json", "summary", 1, "{not-json")

    result = OpsProjectionReader(str(db_path)).read_replay()

    assert result["status"] == "degraded"
    assert result["diagnostics"]["reason"] == "malformed_projection_payload"
    assert result["diagnostics"]["error_type"] == "JSONDecodeError"
    assert result["items"] == []


def test_query_error_returns_degraded_diagnostics(tmp_path):
    db_path = tmp_path / "no-table.db"
    sqlite3.connect(db_path).close()

    result = OpsProjectionReader(str(db_path)).read_system_health()

    assert result["status"] == "degraded"
    assert result["diagnostics"]["reason"] == "query_error"
    assert result["diagnostics"]["error_type"] == "OperationalError"


def test_reader_source_is_read_only_projection_access():
    source = Path("src/services/ops_console/db_projection_reader.py").read_text()

    assert "mode=ro" in source
    assert "DatabaseManager.initialize" not in source
    assert "get_connection" not in source
    for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]:
        assert keyword not in source
