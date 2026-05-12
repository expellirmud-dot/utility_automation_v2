import os
import sys
import hashlib
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from src.services.audit.event_ledger import EventLedger

class DistributedReplayValidator:
    def __init__(self, db_path):
        self.ledger = EventLedger(db_path=db_path)

    def generate_trace_hash(self):
        """Generates a cryptographic hash of the entire event ledger sequence."""
        events = self.ledger.get_all_events()
        
        # We only hash deterministic fields (exclude timestamp and generated IDs if they aren't stable, 
        # but in our system sequence_number and idempotency keys guarantee ordering)
        
        stable_trace = []
        for e in events:
            stable_trace.append({
                "seq": e["sequence_number"],
                "type": e["event_type"],
                "role": e["role"],
                "action": e["action"],
                "decision": e["decision"],
                "state": e["system_state"],
                "idempotency_key": e.get("idempotency_key")
            })
            
        dump = json.dumps(stable_trace, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest(), len(stable_trace)

    def validate_consistency(self, expected_hash, expected_count):
        """Validates that the ledger perfectly matches a known healthy trace."""
        current_hash, current_count = self.generate_trace_hash()
        
        if current_count != expected_count:
            return False, f"Count mismatch. Expected {expected_count}, got {current_count}"
            
        if current_hash != expected_hash:
            return False, f"Hash mismatch. Replay trace diverged from expected baseline."
            
        return True, "Replay trace is bit-consistent."

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "ledger/events.db"
    validator = DistributedReplayValidator(db_path)
    trace_hash, count = validator.generate_trace_hash()
    print(f"Generated Replay Hash for {db_path}: {trace_hash} (Events: {count})")
