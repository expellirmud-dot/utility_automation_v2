from typing import List
from src.models.event_model import DomainEvent

class EventStore:
    def __init__(self):
        self._events: List[DomainEvent] = []

    def append(self, event: DomainEvent):
        self._events.append(event)

    def get_by_aggregate(self, aggregate_id: str):
        return [e for e in self._events if e.aggregate_id == aggregate_id]

    def get_all(self):
        return self._events
