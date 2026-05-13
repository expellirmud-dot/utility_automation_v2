import sqlite3
import json
import os
import gc
from .sequence_manager import SequenceManager

class EventLedger:
    def __init__(self, db_path="ledger/events.db", path=None):
        if path is not None:
            db_path = path
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.sequence_manager = SequenceManager(self.db_path)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, cached_statements=0)

    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.execute("PRAGMA journal_mode=DELETE")
            cursor.close()
            cursor = conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger (
                    sequence_number INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    system_state TEXT NOT NULL,
                    metadata TEXT,
                    idempotency_key TEXT UNIQUE
                )
            """)
            cursor.close()

    def append(self, event, idempotency_key=None):
        """
        Appends an event to the ledger atomically.
        Returns (event_id, sequence_number).
        If idempotency_key already exists, returns existing data.
        """
        try:
            with self._connect() as conn:
                # Check for existing idempotency_key
                if idempotency_key:
                    cursor = conn.execute("SELECT event_id, sequence_number FROM ledger WHERE idempotency_key = ?", (idempotency_key,))
                    try:
                        row = cursor.fetchone()
                    finally:
                        cursor.close()
                    if row:
                        return row[0], row[1]

                seq = self.sequence_manager.next_sequence()
                
                metadata_json = json.dumps(event.metadata) if hasattr(event, 'metadata') else "{}"
                system_state_value = (
                    json.dumps(event.system_state, sort_keys=True)
                    if isinstance(event.system_state, (dict, list))
                    else str(event.system_state)
                )
                
                cursor = conn.execute("""
                    INSERT INTO ledger (
                        sequence_number, event_id, timestamp, event_type, 
                        role, action, decision, system_state, metadata, idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    seq, event.event_id, event.timestamp, event.event_type,
                    event.role, event.action, event.decision, system_state_value,
                    metadata_json, idempotency_key
                ))
                cursor.close()
                return event.event_id, seq
        except sqlite3.IntegrityError:
            # Handle rare race condition where another process inserted the key between check and insert
            with self._connect() as conn:
                cursor = conn.execute("SELECT event_id, sequence_number FROM ledger WHERE idempotency_key = ?", (idempotency_key,))
                try:
                    row = cursor.fetchone()
                finally:
                    cursor.close()
                return row[0], row[1]

    def get_all_events(self):
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM ledger ORDER BY sequence_number ASC")
            try:
                events = []
                for row in cursor:
                    event_dict = dict(row)
                    event_dict['metadata'] = json.loads(event_dict['metadata'])
                    events.append(event_dict)
            finally:
                cursor.close()
        finally:
            conn.close()
        gc.collect()
        return events

    def replay(self):
        return self.get_all_events()
