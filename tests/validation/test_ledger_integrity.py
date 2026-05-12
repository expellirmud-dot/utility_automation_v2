import pytest
import os
from src.services.audit.event_ledger import EventLedger
from src.services.audit.event_models import AuditEvent

def test_ledger_integrity():
    temp_path = "tests/temp_ledger.log"
    ledger = EventLedger(path=temp_path)
    
    # 1. Sequential Append
    ledger.append(AuditEvent("E1", "ROLE", "ACT", "DEC", "STATE", {"data": 1}))
    ledger.append(AuditEvent("E2", "ROLE", "ACT", "DEC", "STATE", {"data": 2}))
    ledger.append(AuditEvent("E3", "ROLE", "ACT", "DEC", "STATE", {"data": 3}))
    
    events = ledger.get_all_events()
    assert len(events) == 3
    assert events[0]["event_type"] == "E1"
    
    # 2. Replay Integrity
    replayed_state = ledger.replay()
    assert len(replayed_state) == 3
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    print("Ledger integrity: PASSED")

if __name__ == "__main__":
    test_ledger_integrity()
