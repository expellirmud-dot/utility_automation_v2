from .sqlite_lock_manager import SQLiteLockManager


SCHEMA_VERSION = 1


class MigrationManager:
    def __init__(self, lock_manager: SQLiteLockManager):
        self.lock_manager = lock_manager

    def migrate(self) -> None:
        with self.lock_manager.write_transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    component TEXT PRIMARY KEY,
                    version INTEGER NOT NULL
                )
            """).close()

            current = conn.execute(
                "SELECT version FROM schema_version WHERE component = ?",
                ("policy_graph",),
            ).fetchone()
            if current and current[0] > SCHEMA_VERSION:
                raise RuntimeError("Policy graph index schema is newer than this runtime")

            self._create_v1_schema(conn)
            conn.execute(
                """
                INSERT INTO schema_version (component, version)
                VALUES (?, ?)
                ON CONFLICT(component) DO UPDATE SET version = excluded.version
                """,
                ("policy_graph", SCHEMA_VERSION),
            ).close()

    def assert_compatible(self) -> None:
        with self.lock_manager.read_connection() as conn:
            row = conn.execute(
                "SELECT version FROM schema_version WHERE component = ?",
                ("policy_graph",),
            ).fetchone()
            if not row:
                raise RuntimeError("Policy graph index schema is not initialized")
            if row[0] != SCHEMA_VERSION:
                raise RuntimeError("Policy graph index schema version mismatch")

    def _create_v1_schema(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_events (
                global_chain_hash TEXT NOT NULL,
                seq_id INTEGER NOT NULL,
                epoch INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_json TEXT NOT NULL
            )
        """).close()
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_policy_events_hash
            ON policy_events(global_chain_hash)
        """).close()
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_policy_events_order
            ON policy_events(epoch, seq_id, global_chain_hash)
        """).close()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_versions (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id TEXT NOT NULL,
                snapshot_hash TEXT NOT NULL,
                stage TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT NOT NULL,
                rollback_target_id TEXT,
                ledger_event_id TEXT NOT NULL,
                ledger_global_hash TEXT NOT NULL,
                ledger_seq_id INTEGER NOT NULL,
                ledger_timestamp TEXT NOT NULL,
                snapshot_json TEXT NOT NULL
            )
        """).close()
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_policy_versions_id
            ON policy_versions(version_id)
        """).close()
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_policy_versions_order
            ON policy_versions(ledger_seq_id, version_id)
        """).close()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_parent_edges (
                parent_version_id TEXT NOT NULL,
                child_version_id TEXT NOT NULL
            )
        """).close()
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_policy_edges_child
            ON policy_parent_edges(child_version_id)
        """).close()
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_policy_edges_parent
            ON policy_parent_edges(parent_version_id)
        """).close()
