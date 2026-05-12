from dataclasses import dataclass, field
from typing import Iterable, Optional, Tuple

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .lineage_explainer import LineageExplainer
from .policy_graph_engine import PolicyGraphEngine
from .policy_version import (
    POLICY_STAGE_PROMOTED,
    POLICY_VERSION_CREATED,
    POLICY_VERSION_ROLLBACK,
    canonicalize,
    stable_hash,
)
from .temporal_reconstructor import TemporalReconstructor


@dataclass(frozen=True)
class ExplanationTransition:
    event_type: str
    version_id: str | None
    from_stage: str | None
    to_stage: str | None
    actor: str | None
    reason: str | None
    quorum_proof: Tuple[str, ...]
    rollback_target_id: str | None
    ledger_global_hash: str
    ledger_seq_id: int
    timestamp: object

    def to_payload(self) -> dict:
        return {
            "event_type": self.event_type,
            "version_id": self.version_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "actor": self.actor,
            "reason": self.reason,
            "quorum_proof": list(self.quorum_proof),
            "rollback_target_id": self.rollback_target_id,
            "ledger_global_hash": self.ledger_global_hash,
            "ledger_seq_id": self.ledger_seq_id,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class GovernanceExplanation:
    version_id: str
    timeline: Tuple[ExplanationTransition, ...]
    actors: Tuple[str, ...]
    approvals: Tuple[str, ...]
    transitions: Tuple[str, ...]
    reasons: Tuple[str, ...]
    quorum_proofs: Tuple[str, ...]
    ledger_evidence_hashes: Tuple[str, ...]
    rollback_target_id: str | None = None
    explanation_hash: str = field(default="")

    def __post_init__(self):
        if not self.explanation_hash:
            object.__setattr__(self, "explanation_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "version_id": self.version_id,
            "timeline": [transition.to_payload() for transition in self.timeline],
            "actors": list(self.actors),
            "approvals": list(self.approvals),
            "transitions": list(self.transitions),
            "reasons": list(self.reasons),
            "quorum_proofs": list(self.quorum_proofs),
            "ledger_evidence_hashes": list(self.ledger_evidence_hashes),
            "rollback_target_id": self.rollback_target_id,
        }
        if include_hash:
            payload["explanation_hash"] = self.explanation_hash
        return canonicalize(payload)


class GovernanceExplanationEngine:
    def __init__(self, events: Optional[Iterable[CanonicalEvent]] = None, graph_engine: Optional[PolicyGraphEngine] = None):
        self.reconstructor = TemporalReconstructor(events, graph_engine)
        self.events = self.reconstructor.events
        self.graph = self.reconstructor.rebuild_graph()

    def explain_version(self, version_id: str) -> GovernanceExplanation:
        version = self.graph.get_version(version_id)
        lineage = LineageExplainer(self.events)
        related_ids = {version_id}
        related_ids.update(ancestor.version_id for ancestor in lineage.ancestors(version_id))

        timeline = []
        for event in self.events:
            transition = self._transition_from_event(event, related_ids)
            if transition:
                timeline.append(transition)

        ordered_timeline = tuple(sorted(timeline, key=lambda t: (t.ledger_seq_id, t.ledger_global_hash)))
        actors = tuple(sorted({t.actor for t in ordered_timeline if t.actor}))
        quorum_proofs = tuple(sorted({proof for t in ordered_timeline for proof in t.quorum_proof}))
        reasons = tuple(sorted({t.reason for t in ordered_timeline if t.reason}))
        transitions = tuple(
            f"{t.from_stage}->{t.to_stage}" for t in ordered_timeline
            if t.from_stage and t.to_stage
        )

        return GovernanceExplanation(
            version_id=version_id,
            timeline=ordered_timeline,
            actors=actors,
            approvals=quorum_proofs,
            transitions=transitions,
            reasons=reasons,
            quorum_proofs=quorum_proofs,
            ledger_evidence_hashes=tuple(t.ledger_global_hash for t in ordered_timeline),
            rollback_target_id=version.rollback_target_id,
        )

    def _transition_from_event(self, event: CanonicalEvent, related_ids: set[str]) -> ExplanationTransition | None:
        event_version_id = self._version_id_for_event(event)
        if event.type in (POLICY_VERSION_CREATED, POLICY_VERSION_ROLLBACK):
            if event_version_id not in related_ids:
                return None
            return ExplanationTransition(
                event_type=event.type,
                version_id=event_version_id,
                from_stage=None,
                to_stage=event.payload.get("stage"),
                actor=event.payload.get("actor") or event.actor or None,
                reason=event.payload.get("reason"),
                quorum_proof=(),
                rollback_target_id=event.payload.get("rollback_target_id"),
                ledger_global_hash=event.global_chain_hash,
                ledger_seq_id=event.seq_id,
                timestamp=event.timestamp,
            )

        if event.type == POLICY_STAGE_PROMOTED:
            version_id = event.payload.get("version_id")
            if version_id not in related_ids:
                return None
            return ExplanationTransition(
                event_type=event.type,
                version_id=version_id,
                from_stage=event.payload.get("from_stage"),
                to_stage=event.payload.get("to_stage"),
                actor=event.payload.get("actor") or event.actor or None,
                reason=None,
                quorum_proof=tuple(sorted(event.payload.get("quorum_proof", []))),
                rollback_target_id=None,
                ledger_global_hash=event.global_chain_hash,
                ledger_seq_id=event.seq_id,
                timestamp=event.timestamp,
            )
        return None

    def _version_id_for_event(self, event: CanonicalEvent) -> str | None:
        for version in self.graph.versions.values():
            if version.ledger_global_hash == event.global_chain_hash:
                return version.version_id
        return None
