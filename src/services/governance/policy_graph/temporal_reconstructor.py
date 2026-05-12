from typing import Any, Iterable, Optional

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .policy_graph_engine import PolicyGraphEngine
from .policy_version import PolicySnapshot


class TemporalReconstructor:
    def __init__(self, events: Optional[Iterable[CanonicalEvent]] = None, graph_engine: Optional[PolicyGraphEngine] = None):
        if events is None and graph_engine is not None:
            events = graph_engine.transition_events
        self.events = self._canonical_events(events or [])

    def policy_at_timestamp(self, timestamp: Any) -> PolicySnapshot:
        probe = PolicyGraphEngine()
        cutoff = probe._timestamp_sort_key(timestamp)
        filtered_events = [
            event for event in self.events
            if probe._timestamp_sort_key(event.timestamp) <= cutoff
        ]
        graph = PolicyGraphEngine.rebuild_from_ledger(filtered_events)
        head = graph.current_head()
        return head.snapshot if head else PolicySnapshot()

    def policy_at_version(self, version_id: str) -> PolicySnapshot:
        graph = PolicyGraphEngine.rebuild_from_ledger(self.events)
        return graph.get_version(version_id).snapshot

    def graph_at_timestamp(self, timestamp: Any) -> PolicyGraphEngine:
        probe = PolicyGraphEngine()
        cutoff = probe._timestamp_sort_key(timestamp)
        return PolicyGraphEngine.rebuild_from_ledger(
            event for event in self.events
            if probe._timestamp_sort_key(event.timestamp) <= cutoff
        )

    def rebuild_graph(self) -> PolicyGraphEngine:
        return PolicyGraphEngine.rebuild_from_ledger(self.events)

    def _canonical_events(self, events: Iterable[CanonicalEvent]):
        probe = PolicyGraphEngine()
        return [
            event for event in sorted(events, key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash))
            if probe._is_committed_policy_event(event)
        ]
