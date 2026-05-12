import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from src.models.event_model import DomainEvent
from src.services.event_sourcing.event_store import EventStore
from src.services.event_sourcing.replay_engine import ReplayEngine
from src.services.event_sourcing.event_sourcing_service import EventSourcingService

def test_event_store():
    store = EventStore()
    assert len(store.get_all()) == 0
    
    event = DomainEvent(
        event_id="evt_1",
        aggregate_id="agg_1",
        event_type="VOUCHER_CREATED",
        payload={"amount": 100},
        timestamp=datetime.now(timezone.utc),
        version=1
    )
    store.append(event)
    assert len(store.get_all()) == 1
    assert len(store.get_by_aggregate("agg_1")) == 1

def test_replay_engine():
    engine = ReplayEngine()
    assert isinstance(engine.rebuild_state([]), dict)
    
    events = [
        DomainEvent(
            event_id="1", aggregate_id="agg_1", event_type="VOUCHER_CREATED",
            payload={"id": "v1", "amount": 100}, timestamp=datetime.now(timezone.utc), version=1
        ),
        DomainEvent(
            event_id="2", aggregate_id="agg_1", event_type="FINANCIAL_VALIDATED",
            payload={"status": "PASS"}, timestamp=datetime.now(timezone.utc), version=1
        )
    ]
    state = engine.rebuild_state(events)
    assert state["id"] == "v1"
    assert state["amount"] == 100
    assert state["financial"]["status"] == "PASS"

def test_simulation():
    service = EventSourcingService()
    
    # Setup initial state
    service.emit(DomainEvent(
        event_id="evt_1", aggregate_id="voucher_1", event_type="VOUCHER_CREATED",
        payload={"id": "voucher_1"}, timestamp=datetime.now(timezone.utc), version=1
    ))
    
    # Simulate adding new decision
    new_events = [DomainEvent(
        event_id="evt_2", aggregate_id="voucher_1", event_type="DECISION_MADE",
        payload={"governance_decision": "ALLOW"}, timestamp=datetime.now(timezone.utc), version=1
    )]
    
    result = service.simulate("voucher_1", new_events)
    
    assert "analysis" in result
    assert "simulation" in result
    assert result["simulation"]["simulated_state"].get("decision", {}).get("governance_decision") == "ALLOW"
    assert result["analysis"]["impact_level"] in ["LOW", "MEDIUM", "HIGH"]
