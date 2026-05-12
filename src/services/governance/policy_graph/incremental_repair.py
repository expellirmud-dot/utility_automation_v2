from dataclasses import dataclass
from typing import Iterable

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .index_integrity_checker import IndexIntegrityChecker
from .policy_graph_engine import PolicyGraphEngine


FULL_REBUILD_REASONS = {
    "TIMESTAMP_ORDER_CORRUPTION",
}


@dataclass(frozen=True)
class RepairResult:
    graph: PolicyGraphEngine
    repaired: bool
    mode: str
    reason: str


class IncrementalRepair:
    def __init__(self, store):
        self.store = store
        self.integrity_checker = IndexIntegrityChecker(store)

    def repair(self, ledger_events: Iterable[CanonicalEvent]) -> RepairResult:
        ledger_events = list(ledger_events)
        result = self.integrity_checker.verify(ledger_events)
        if result.ok:
            return RepairResult(
                PolicyGraphEngine.rebuild_from_ledger(self.store.load_events()),
                False,
                "UNCHANGED",
                result.reason,
            )

        ledger_graph = PolicyGraphEngine.rebuild_from_ledger(ledger_events)
        if result.reason in FULL_REBUILD_REASONS:
            self.store.replace_from_projection(ledger_graph.versions.values(), ledger_graph.transition_events)
            return RepairResult(ledger_graph, True, "FULL_REBUILD", result.reason)

        self.store.repair_from_projection(ledger_graph.versions.values(), ledger_graph.transition_events)
        post_repair = self.integrity_checker.verify(ledger_events)
        if post_repair.ok:
            return RepairResult(ledger_graph, True, "INCREMENTAL_REPAIR", result.reason)

        self.store.replace_from_projection(ledger_graph.versions.values(), ledger_graph.transition_events)
        return RepairResult(ledger_graph, True, "FULL_REBUILD", post_repair.reason)
