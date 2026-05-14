from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import sqlite3


DOMAIN_TABLES: dict[str, tuple[str, ...]] = {
    "recovery": ("recovery_projection", "recovery_projections", "recovery_read_model"),
    "simulation": ("simulation_projection", "simulation_projections", "simulation_read_model"),
    "mesh": ("mesh_projection", "mesh_projections"),
    "policy": ("policy_projection", "policy_projections", "policy_read_model"),
    "replay": ("replay_projection", "replay_projections"),
    "system_health": (
        "system_health_projection",
        "system_health_projections",
        "system_health_telemetry",
    ),
}

STABLE_ROW_KEYS = (
    "stable_order",
    "epoch",
    "seq_id",
    "sequence",
    "id",
    "key",
    "event_hash",
    "hash",
    "artifact_hash",
    "domain",
)


@dataclass(frozen=True)
class ProjectionReadResult:
    domain: str
    status: str
    source: str
    items: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    metadata: dict[str, Any]


class DBProjectionReader:
    def __init__(self, db_path: str | Path | None = None) -> None:
        raw_path = db_path or os.getenv("OPS_PROJECTION_DB_PATH") or "data/utility_automation.db"
        self._db_path = Path(raw_path)

    def read_recovery(self) -> ProjectionReadResult:
        return self.read_domain("recovery")

    def read_simulation(self) -> ProjectionReadResult:
        return self.read_domain("simulation")

    def read_mesh(self) -> ProjectionReadResult:
        return self.read_domain("mesh")

    def read_policy(self) -> ProjectionReadResult:
        return self.read_domain("policy")

    def read_replay(self) -> ProjectionReadResult:
        return self.read_domain("replay")

    def read_system_health(self) -> ProjectionReadResult:
        return self.read_domain("system_health")

    def read_domain(self, domain: str) -> ProjectionReadResult:
        if domain not in DOMAIN_TABLES:
            return self._fallback(domain, reason="unknown_domain", detail=domain)

        if not self._db_path.exists():
            return self._fallback(domain, reason="missing_database", detail=self._db_path.name)

        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                table_name = self._find_table(conn, DOMAIN_TABLES[domain])
                if table_name is None:
                    return self._empty(domain, reason="table_missing")

                rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
                items = tuple(sorted((self._normalize_row(row) for row in rows), key=self._row_sort_key))
                return ProjectionReadResult(
                    domain=domain,
                    status="connected" if items else "empty",
                    source="database_projection",
                    items=items,
                    diagnostics={
                        "connected": True,
                        "degraded": False,
                        "reason": "ok" if items else "empty_table",
                    },
                    metadata=self._metadata(table_name=table_name),
                )
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            return self._fallback(domain, reason="query_error", detail=exc.__class__.__name__)

    def _connect(self) -> sqlite3.Connection:
        uri = f"{self._db_path.resolve().as_uri()}?mode=ro"
        return sqlite3.connect(uri, uri=True, cached_statements=0)

    def _find_table(self, conn: sqlite3.Connection, candidates: tuple[str, ...]) -> str | None:
        for table_name in candidates:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
                ("table", table_name),
            ).fetchone()
            if row is not None:
                return table_name
        return None

    def _normalize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key in sorted(row.keys()):
            value = row[key]
            if isinstance(value, bytes):
                normalized[key] = value.hex()
            elif value is None or isinstance(value, (str, int, float, bool)):
                normalized[key] = value
            else:
                normalized[key] = str(value)
        return normalized

    def _row_sort_key(self, item: dict[str, Any]) -> tuple[str, ...]:
        stable_values = tuple(str(item.get(key, "")) for key in STABLE_ROW_KEYS)
        canonical = json.dumps(item, sort_keys=True, separators=(",", ":"), default=str)
        return (*stable_values, canonical)

    def _fallback(self, domain: str, *, reason: str, detail: str) -> ProjectionReadResult:
        return ProjectionReadResult(
            domain=domain,
            status="degraded",
            source="deterministic_fallback",
            items=(),
            diagnostics={
                "connected": False,
                "degraded": True,
                "reason": reason,
                "detail": detail,
            },
            metadata=self._metadata(table_name=None),
        )

    def _empty(self, domain: str, *, reason: str) -> ProjectionReadResult:
        return ProjectionReadResult(
            domain=domain,
            status="empty",
            source="database_projection",
            items=(),
            diagnostics={
                "connected": True,
                "degraded": False,
                "reason": reason,
            },
            metadata=self._metadata(table_name=None),
        )

    def _metadata(self, *, table_name: str | None) -> dict[str, Any]:
        return {
            "read_only": True,
            "projection_only": True,
            "database_role": "cache_projection",
            "source_of_truth": "ledger",
            "table": table_name,
        }
