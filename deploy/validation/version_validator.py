import json
import os
import hashlib

class SchemaValidator:
    LEDGER_SCHEMA_VERSION = "v1.0.0"
    RULE_SCHEMA_VERSION = "v1.0.0"

    @classmethod
    def validate_ledger_schema(cls, db_path):
        """Ensures the SQLite ledger schema is compatible with the running service."""
        import sqlite3
        if not os.path.exists(db_path):
            return True # New DB is fine
            
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(ledger)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # Require these exact columns for v1.0.0
            required = {
                "sequence_number": "INTEGER",
                "event_id": "TEXT",
                "timestamp": "TEXT",
                "event_type": "TEXT",
                "role": "TEXT",
                "action": "TEXT",
                "decision": "TEXT",
                "system_state": "TEXT",
                "metadata": "TEXT",
                "idempotency_key": "TEXT"
            }
            
            for col, dtype in required.items():
                if col not in columns:
                    raise RuntimeError(f"Schema mismatch: missing column {col}")

    @classmethod
    def validate_rule_schema(cls, rules):
        """Ensures loaded rules conform to the expected deterministic schema."""
        for rule in rules:
            if not hasattr(rule, 'priority') or not hasattr(rule, 'effect'):
                raise RuntimeError(f"Rule schema mismatch: {rule} missing required deterministic fields.")
                
    @classmethod
    def generate_runtime_hash(cls):
        """Generates a hash of the current runtime configuration to detect version mismatches across nodes."""
        config_state = f"{cls.LEDGER_SCHEMA_VERSION}:{cls.RULE_SCHEMA_VERSION}"
        return hashlib.sha256(config_state.encode()).hexdigest()
