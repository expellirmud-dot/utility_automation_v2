import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from src.services.global_consistency.budget_constraint_engine import BudgetConstraintEngine
from src.services.global_consistency.cross_voucher_validator import CrossVoucherValidator
from src.services.global_consistency.policy_conflict_detector import PolicyConflictDetector
from src.services.global_consistency.system_reconciler import SystemReconciler
from src.models.global_state import GlobalState
from src.services.event_sourcing.event_store import EventStore
from src.models.event_model import DomainEvent

def test_budget_constraint():
    engine = BudgetConstraintEngine()

    class GS:
        total_budget = 100
        used_budget = 200
        def remaining_budget(self): return -100

    result = engine.validate(GS())
    assert "BUDGET_EXCEEDED" in result
    assert "NEGATIVE_BUDGET_STATE" in result

def test_cross_voucher():
    validator = CrossVoucherValidator()

    vouchers = [
        {"vendor": "A", "amount": 100, "net": 100, "budget_line": "X"},
        {"vendor": "A", "amount": 100, "net": 100, "budget_line": "X"}
    ]

    issues = validator.validate(vouchers)
    assert "POSSIBLE_DUPLICATE_PAYMENT" in issues

def test_policy_conflict():
    detector = PolicyConflictDetector()
    rules = [
        {"id": "r1", "type": "APPROVAL_LIMIT", "value": 5000},
        {"id": "r2", "type": "APPROVAL_LIMIT", "value": 10000}
    ]
    conflicts = detector.detect(rules)
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "CONFLICT_LIMIT"

def test_system_reconciler():
    reconciler = SystemReconciler()
    store = EventStore()
    
    # Payload simulating decision made
    store.append(DomainEvent(
        event_id="1", aggregate_id="a1", event_type="DECISION_MADE",
        payload={"net": 500}, timestamp=datetime.now(timezone.utc), version=1
    ))
    
    state = GlobalState(total_budget=1000, used_budget=400) # Inconsistent! State says 400, events say 500
    
    corrections = reconciler.reconcile(state, store)
    assert len(corrections) == 1
    assert corrections[0]["type"] == "BUDGET_MISMATCH"
    assert corrections[0]["expected"] == 500
    assert corrections[0]["actual"] == 400
