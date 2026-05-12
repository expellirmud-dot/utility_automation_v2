from src.services.event_sourcing.event_store import EventStore
from src.services.event_sourcing.replay_engine import ReplayEngine
from src.services.event_sourcing.simulation_engine import SimulationEngine
from src.services.event_sourcing.what_if_analyzer import WhatIfAnalyzer
from src.models.event_model import DomainEvent

class EventSourcingService:
    def __init__(self):
        self.store = EventStore()
        self.replay = ReplayEngine()
        self.simulation = SimulationEngine(self.store)
        self.analyzer = WhatIfAnalyzer()

    def emit(self, event: DomainEvent):
        self.store.append(event)

    def reconstruct(self, aggregate_id: str):
        events = self.store.get_by_aggregate(aggregate_id)
        return self.replay.rebuild_state(events)

    def simulate(self, aggregate_id: str, new_events: list[DomainEvent]):
        result = self.simulation.simulate_rule_change(
            aggregate_id,
            new_events
        )

        analysis = self.analyzer.analyze(result)

        return {
            "simulation": result,
            "analysis": analysis
        }
