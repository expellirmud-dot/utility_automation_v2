import sqlite3
import threading

class SequenceManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, cached_statements=0)

    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.execute("""
                CREATE TABLE IF NOT EXISTS sequences (
                    name TEXT PRIMARY KEY,
                    value INTEGER DEFAULT 0
                )
            """)
            cursor.close()
            cursor = conn.execute("INSERT OR IGNORE INTO sequences (name, value) VALUES ('audit_events', 0)")
            cursor.close()

    def next_sequence(self):
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute("UPDATE sequences SET value = value + 1 WHERE name = 'audit_events' RETURNING value")
                try:
                    row = cursor.fetchone()
                finally:
                    cursor.close()
                conn.commit()
                if row:
                    return row[0]
                return 1
