from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.storage.database.database_manager import DatabaseManager


DOMAIN_BUCKETS = {
    "recovery": "ops_recovery",
    "simulation": "ops_simulation",
    "mesh": "ops_mesh",
    "policy": "ops_policy",
    "replay": "ops_replay",
    "system_health": "ops_system_health",
}


class OpsProjectionReader:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or DatabaseManager.DB_PATH

    def read_recovery(self) -> dict[str, Any]:
        return self.read_domain("recovery")

    def read_simulation(self) -> dict[str, Any]:
        return self.read_domain("simulation")

    def read_mesh(self) -> dict[str, Any]:
        return self.read_domain("mesh")

    def read_policy(self) -> dict[str, Any]:
        return self.read_domain("policy")

    def read_replay(self) -> dict[str, Any]:
        return self.read_domain("replay")

    def read_system_health(self) -> dict[str, Any]:
        return self.read_domain("system_health")

    def read_all(self) -> dict[str, dict[str, Any]]:
        return {
            "recovery": self.read_recovery(),
            "simulation": self.read_simulation(),
            "mesh": self.read_mesh(),
            "policy": self.read_policy(),
            "replay": self.read_replay(),
            "system_health": self.read_system_health(),
        }

    def read_domain(self, domain: str) -> dict[str, Any]:
        if domain not in DOMAIN_BUCKETS:
            return _degraded_result(domain, f"ops_{domain}", "unknown_domain")

        bucket = DOMAIN_BUCKETS[domain]
        path = Path(self._db_path)
        if not path.exists():
            return _degraded_result(domain, bucket, "database_missing")

        try:
            conn = _connect_read_only(path)
            conn.row_factory = _sqlite_row_factory
            try:
                rows = conn.execute(
                    """
                    SELECT bucket, stable_key, record_type, sort_order, payload_json
                    FROM dashboard_projection_records
                    WHERE bucket = ?
                    ORDER BY record_type, sort_order, stable_key
                    """,
                    (bucket,),
                ).fetchall()
            finally:
                conn.close()
        except sqlite3.Error as exc:
            return _degraded_result(domain, bucket, "query_error", exc)

        try:
            items = [_row_to_item(row) for row in rows]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return _degraded_result(domain, bucket, "malformed_projection_payload", exc)

        return {
            "domain": domain,
            "bucket": bucket,
            "status": "connected",
            "degraded": False,
            "item_count": len(items),
            "items": items,
            "diagnostics": {
                "source": "sqlite_projection",
                "projection_only": True,
                "status": "connected",
                "reason": "ok",
            },
            "metadata": {
                "database": "sqlite",
                "bucket": bucket,
                "ordering": "record_type, sort_order, stable_key",
            },
        }


def _connect_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def _row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "bucket": str(row["bucket"]),
        "stable_key": str(row["stable_key"]),
        "record_type": str(row["record_type"]),
        "sort_order": int(row["sort_order"]),
        "payload": json.loads(row["payload_json"]),
    }


def _degraded_result(
    domain: str,
    bucket: str,
    reason: str,
    exc: Exception | None = None,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "source": "sqlite_projection",
        "projection_only": True,
        "status": "degraded",
        "reason": reason,
    }
    if exc is not None:
        diagnostics["error_type"] = exc.__class__.__name__

    return {
        "domain": domain,
        "bucket": bucket,
        "status": "degraded",
        "degraded": True,
        "item_count": 0,
        "items": [],
        "diagnostics": diagnostics,
        "metadata": {
            "database": "sqlite",
            "bucket": bucket,
            "ordering": "record_type, sort_order, stable_key",
        },
    }


def _sqlite_row_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {description[0]: row[index] for index, description in enumerate(cursor.description)}
