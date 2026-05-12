import json
import os
from typing import Iterable, List

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .migration_manager import MigrationManager
from .policy_graph_store import PolicyGraphStore
from .policy_version import PolicyVersion, canonical_json
from .sqlite_lock_manager import SQLiteLockManager


class SQLitePolicyGraphStore(PolicyGraphStore):
    def __init__(self, db_path: str, busy_timeout_ms: int = 5000):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.lock_manager = SQLiteLockManager(db_path, busy_timeout_ms)
        self.migration_manager = MigrationManager(self.lock_manager)
        self.migration_manager.migrate()
        self.migration_manager.assert_compatible()

    def _connect(self):
        return self.lock_manager.connect()

    def replace_from_projection(self, versions: Iterable[PolicyVersion], events: Iterable[CanonicalEvent]) -> None:
        versions = list(versions)
        events = list(events)
        with self.lock_manager.write_transaction() as conn:
            conn.execute("DELETE FROM policy_parent_edges").close()
            conn.execute("DELETE FROM policy_versions").close()
            conn.execute("DELETE FROM policy_events").close()
            self._insert_events(conn, events)
            self._insert_versions(conn, versions)

    def repair_from_projection(self, versions: Iterable[PolicyVersion], events: Iterable[CanonicalEvent]) -> None:
        versions = list(versions)
        events = list(events)
        version_ids = {version.version_id for version in versions}
        event_hashes = {event.global_chain_hash for event in events}

        with self.lock_manager.write_transaction() as conn:
            self._insert_events(conn, events)
            self._upsert_versions(conn, versions)

            if event_hashes:
                placeholders = ",".join("?" for _ in event_hashes)
                conn.execute(
                    f"DELETE FROM policy_events WHERE global_chain_hash NOT IN ({placeholders})",
                    tuple(sorted(event_hashes)),
                ).close()
            else:
                conn.execute("DELETE FROM policy_events").close()

            if version_ids:
                placeholders = ",".join("?" for _ in version_ids)
                conn.execute(
                    f"DELETE FROM policy_versions WHERE version_id NOT IN ({placeholders})",
                    tuple(sorted(version_ids)),
                ).close()
                conn.execute(
                    f"""
                    DELETE FROM policy_parent_edges
                    WHERE child_version_id NOT IN ({placeholders})
                    OR parent_version_id NOT IN ({placeholders})
                    """,
                    tuple(sorted(version_ids)) * 2,
                ).close()
            else:
                conn.execute("DELETE FROM policy_versions").close()
                conn.execute("DELETE FROM policy_parent_edges").close()

            for version in versions:
                conn.execute(
                    "DELETE FROM policy_parent_edges WHERE child_version_id = ?",
                    (version.version_id,),
                ).close()
                for parent_id in version.parent_version_ids:
                    conn.execute(
                        """
                        INSERT INTO policy_parent_edges (parent_version_id, child_version_id)
                        VALUES (?, ?)
                        """,
                        (parent_id, version.version_id),
                    ).close()

    def load_events(self) -> List[CanonicalEvent]:
        with self.lock_manager.read_connection() as conn:
            conn.row_factory = self._row_factory()
            cursor = conn.execute("SELECT event_json FROM policy_events ORDER BY epoch, seq_id, global_chain_hash")
            try:
                rows = cursor.fetchall()
            finally:
                cursor.close()

        return [CanonicalEvent(**json.loads(row["event_json"])) for row in rows]

    def load_versions(self) -> List[dict]:
        with self.lock_manager.read_connection() as conn:
            conn.row_factory = self._row_factory()
            cursor = conn.execute("SELECT * FROM policy_versions ORDER BY ledger_seq_id, version_id, row_id")
            try:
                return [dict(row) for row in cursor.fetchall()]
            finally:
                cursor.close()

    def load_parent_edges(self) -> List[dict]:
        with self.lock_manager.read_connection() as conn:
            conn.row_factory = self._row_factory()
            cursor = conn.execute("SELECT * FROM policy_parent_edges ORDER BY parent_version_id, child_version_id")
            try:
                return [dict(row) for row in cursor.fetchall()]
            finally:
                cursor.close()

    def load_schema_version(self) -> int:
        with self.lock_manager.read_connection() as conn:
            row = conn.execute(
                "SELECT version FROM schema_version WHERE component = ?",
                ("policy_graph",),
            ).fetchone()
            return row[0] if row else 0

    def clear(self) -> None:
        with self.lock_manager.write_transaction() as conn:
            conn.execute("DELETE FROM policy_parent_edges").close()
            conn.execute("DELETE FROM policy_versions").close()
            conn.execute("DELETE FROM policy_events").close()

    def _insert_events(self, conn, events: Iterable[CanonicalEvent]) -> None:
        for event in sorted(events, key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash)):
            conn.execute(
                """
                INSERT INTO policy_events (global_chain_hash, seq_id, epoch, event_type, event_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(global_chain_hash) DO UPDATE SET
                    seq_id = excluded.seq_id,
                    epoch = excluded.epoch,
                    event_type = excluded.event_type,
                    event_json = excluded.event_json
                """,
                (
                    event.global_chain_hash,
                    event.seq_id,
                    event.epoch,
                    event.type,
                    canonical_json(event.__dict__),
                ),
            ).close()

    def _insert_versions(self, conn, versions: Iterable[PolicyVersion]) -> None:
        for version in sorted(versions, key=lambda v: (v.ledger_seq_id, v.version_id)):
            self._insert_version_row(conn, version)
            for parent_id in version.parent_version_ids:
                conn.execute(
                    """
                    INSERT INTO policy_parent_edges (parent_version_id, child_version_id)
                    VALUES (?, ?)
                    """,
                    (parent_id, version.version_id),
                ).close()

    def _upsert_versions(self, conn, versions: Iterable[PolicyVersion]) -> None:
        for version in sorted(versions, key=lambda v: (v.ledger_seq_id, v.version_id)):
            conn.execute(
                "DELETE FROM policy_versions WHERE version_id = ?",
                (version.version_id,),
            ).close()
            self._insert_version_row(conn, version)

    def _insert_version_row(self, conn, version: PolicyVersion) -> None:
        conn.execute(
            """
            INSERT INTO policy_versions (
                version_id, snapshot_hash, stage, actor, reason, rollback_target_id,
                ledger_event_id, ledger_global_hash, ledger_seq_id, ledger_timestamp, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version.version_id,
                version.snapshot.snapshot_hash,
                version.stage,
                version.actor,
                version.reason,
                version.rollback_target_id,
                version.ledger_event_id,
                version.ledger_global_hash,
                version.ledger_seq_id,
                str(version.ledger_timestamp),
                canonical_json(version.snapshot.to_payload()),
            ),
        ).close()

    def _row_factory(self):
        import sqlite3
        return sqlite3.Row
