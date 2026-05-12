from typing import Dict, List
from src.models.event_model import DomainEvent

class ReplayEngine:
    def rebuild_state(self, events: List[DomainEvent]) -> Dict:
        state = {}

        for event in events:
            if event.event_type == "VOUCHER_CREATED":
                state = event.payload.copy()
            elif event.event_type == "FINANCIAL_VALIDATED":
                state["financial"] = event.payload.copy()
            elif event.event_type == "COMPLIANCE_CHECKED":
                state["compliance"] = event.payload.copy()
            elif event.event_type == "DECISION_MADE":
                state["decision"] = event.payload.copy()

        return state
