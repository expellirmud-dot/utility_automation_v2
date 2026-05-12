import sqlite3
from contextlib import contextmanager


class SQLiteLockManager:
    def __init__(self, db_path: str, busy_timeout_ms: int = 5000):
        self.db_path = db_path
        self.busy_timeout_ms = busy_timeout_ms

    def connect(self):
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.busy_timeout_ms / 1000,
            cached_statements=0,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}").close()
        conn.execute("PRAGMA journal_mode=WAL").close()
        conn.execute("PRAGMA synchronous=NORMAL").close()
        conn.execute("PRAGMA foreign_keys=ON").close()
        return conn

    @contextmanager
    def read_connection(self):
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def write_transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE").close()
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
