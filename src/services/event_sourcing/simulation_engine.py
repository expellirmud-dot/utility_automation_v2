import copy
from src.services.event_sourcing.event_store import EventStore
from src.services.event_sourcing.replay_engine import ReplayEngine
from src.models.event_model import DomainEvent

class SimulationEngine:
    def __init__(self, store: EventStore):
        self.store = store
        self.replay_engine = ReplayEngine()

    def simulate_rule_change(self, aggregate_id: str, new_rule_events: list[DomainEvent]):
        """
        จำลองผลของ rule ใหม่โดยไม่กระทบ production data
        """
        original_events = self.store.get_by_aggregate(aggregate_id)

        # original state
        original_state = self.replay_engine.rebuild_state(original_events)

        # simulated state
        simulated_events = copy.deepcopy(original_events)
        simulated_events.extend(new_rule_events)

        simulated_state = self.replay_engine.rebuild_state(simulated_events)

        return {
            "original_state": original_state,
            "simulated_state": simulated_state,
            "diff": self._diff(original_state, simulated_state)
        }

    def _diff(self, a, b):
        return {
            "changed_fields": list(set(a.keys()) ^ set(b.keys()))
        }
