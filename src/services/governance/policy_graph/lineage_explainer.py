from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .policy_graph_engine import PolicyGraphEngine
from .policy_version import POLICY_STAGE_PROMOTED
from .temporal_reconstructor import TemporalReconstructor


@dataclass(frozen=True)
class PromotionTransition:
    version_id: str
    from_stage: str
    to_stage: str
    actor: str | None
    quorum_proof: Tuple[str, ...]
    ledger_global_hash: str
    ledger_seq_id: int
    timestamp: object


class LineageExplainer:
    def __init__(self, events: Optional[Iterable[CanonicalEvent]] = None, graph_engine: Optional[PolicyGraphEngine] = None):
        self.reconstructor = TemporalReconstructor(events, graph_engine)
        self.events = self.reconstructor.events
        self.graph = self.reconstructor.rebuild_graph()

    def ancestors(self, version_id: str):
        visited = set()
        result = []

        def visit(current_id: str):
            version = self.graph.get_version(current_id)
            for parent_id in sorted(version.parent_version_ids):
                if parent_id in visited:
                    continue
                visited.add(parent_id)
                visit(parent_id)
                result.append(self.graph.get_version(parent_id))

        visit(version_id)
        return tuple(sorted(result, key=lambda v: (v.ledger_seq_id, v.version_id)))

    def descendants(self, version_id: str):
        result = []
        queue = list(sorted(self.graph.children.get(version_id, [])))
        seen = set()
        while queue:
            child_id = queue.pop(0)
            if child_id in seen:
                continue
            seen.add(child_id)
            child = self.graph.get_version(child_id)
            result.append(child)
            queue.extend(sorted(self.graph.children.get(child_id, [])))
        return tuple(sorted(result, key=lambda v: (v.ledger_seq_id, v.version_id)))

    def rollback_ancestry(self, version_id: str):
        result = []
        seen = set()
        current = self.graph.get_version(version_id)
        while current.rollback_target_id:
            if current.version_id in seen:
                raise ValueError(f"Rollback ancestry cycle detected at {current.version_id}")
            seen.add(current.version_id)
            target = self.graph.get_version(current.rollback_target_id)
            if target.version_id in seen:
                raise ValueError(f"Rollback ancestry cycle detected at {target.version_id}")
            result.append(target)
            current = target
        return tuple(result)

    def promotion_lineage(self, version_id: str):
        transitions = []
        for event in self.events:
            if event.type != POLICY_STAGE_PROMOTED:
                continue
            if event.payload.get("version_id") != version_id:
                continue
            transitions.append(PromotionTransition(
                version_id=version_id,
                from_stage=event.payload.get("from_stage"),
                to_stage=event.payload.get("to_stage"),
                actor=event.payload.get("actor"),
                quorum_proof=tuple(sorted(event.payload.get("quorum_proof", []))),
                ledger_global_hash=event.global_chain_hash,
                ledger_seq_id=event.seq_id,
                timestamp=event.timestamp,
            ))
        return tuple(sorted(transitions, key=lambda t: (t.ledger_seq_id, t.ledger_global_hash)))
