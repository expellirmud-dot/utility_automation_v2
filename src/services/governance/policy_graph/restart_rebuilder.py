from typing import Iterable

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .index_integrity_checker import IndexIntegrityChecker
from .incremental_repair import IncrementalRepair
from .policy_graph_engine import PolicyGraphEngine


class RestartRebuilder:
    def __init__(self, store):
        self.store = store
        self.integrity_checker = IndexIntegrityChecker(store)
        self.incremental_repair = IncrementalRepair(store)

    def rebuild_index_from_ledger(self, ledger_events: Iterable[CanonicalEvent]) -> PolicyGraphEngine:
        graph = PolicyGraphEngine.rebuild_from_ledger(ledger_events)
        self.store.replace_from_projection(graph.versions.values(), graph.transition_events)
        return graph

    def load_graph_from_index(self) -> PolicyGraphEngine:
        return PolicyGraphEngine.rebuild_from_ledger(self.store.load_events())

    def rebuild_or_verify(self, ledger_events: Iterable[CanonicalEvent]) -> PolicyGraphEngine:
        ledger_events = list(ledger_events)
        return self.incremental_repair.repair(ledger_events).graph
