from dataclasses import dataclass, field
from typing import Optional, Tuple

from src.services.governance.recovery.recovery_handoff import (
    RecoveryAuthorityDecision,
    RecoveryHandoffDecision,
)
from src.services.governance.recovery.recovery_models import RecoveryProposal
from src.services.governance.recovery.recovery_report_hasher import stable_hash
from src.services.governance.recovery.recovery_simulation_gate import (
    RecoverySimulationReport,
    RecoverySimulationRiskLevel,
)


SIGNAL_DETECTED = 1
CLASSIFIED = 2
PLAN_BUILT = 3
SIMULATION_COMPLETED = 4
AUTHORITY_HANDOFF = 5
AUTHORITY_DECISION = 6

EVENT_SIGNAL = "signal"
EVENT_CLASSIFICATION = "classification"
EVENT_PLAN = "plan"
EVENT_SIMULATION = "simulation"
EVENT_HANDOFF = "handoff"
EVENT_DECISION = "decision"


@dataclass(frozen=True)
class RecoveryTimelineEvent:
    sequence: int
    event_type: str
    proposal_hash: str
    artifact_hash: str
    detail_code: str
    event_hash: str = field(default="")

    def __post_init__(self):
        if not self.event_hash:
            object.__setattr__(self, "event_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "artifact_hash": self.artifact_hash,
            "detail_code": self.detail_code,
            "event_type": self.event_type,
            "proposal_hash": self.proposal_hash,
            "sequence": self.sequence,
        }
        if include_hash:
            payload["event_hash"] = self.event_hash
        return payload


@dataclass(frozen=True)
class RecoveryTimeline:
    proposal_hash: str
    events: Tuple[RecoveryTimelineEvent, ...]
    timeline_hash: str = field(default="")

    def __post_init__(self):
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda item: (
            item.sequence,
            item.event_type,
            item.artifact_hash,
            item.detail_code,
        ))))
        if not self.timeline_hash:
            object.__setattr__(self, "timeline_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "events": [item.to_payload(include_hash=True) for item in self.events],
            "proposal_hash": self.proposal_hash,
        }
        if include_hash:
            payload["timeline_hash"] = self.timeline_hash
        return payload


@dataclass(frozen=True)
class RecoveryAnalyticsSnapshot:
    total_proposals: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    deferred_count: int = 0
    blocked_simulations: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    analytics_hash: str = field(default="")

    def __post_init__(self):
        if not self.analytics_hash:
            object.__setattr__(self, "analytics_hash", stable_hash(self.to_hash_payload()))

    def to_hash_payload(self) -> dict:
        return {
            "approved_count": self.approved_count,
            "blocked_simulations": self.blocked_simulations,
            "deferred_count": self.deferred_count,
            "high_risk_count": self.high_risk_count,
            "low_risk_count": self.low_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "rejected_count": self.rejected_count,
            "total_proposals": self.total_proposals,
        }

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = self.to_hash_payload()
        if include_hash:
            payload["analytics_hash"] = self.analytics_hash
        return payload


@dataclass(frozen=True)
class RecoveryArtifactRegistry:
    proposals: Tuple[RecoveryProposal, ...] = ()
    simulations: Tuple[RecoverySimulationReport, ...] = ()
    handoffs: Tuple[RecoveryHandoffDecision, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "proposals", _sort_proposals(self.proposals))
        object.__setattr__(self, "simulations", _sort_simulations(self.simulations))
        object.__setattr__(self, "handoffs", _sort_handoffs(self.handoffs))

    def register_proposal(self, proposal: RecoveryProposal) -> "RecoveryArtifactRegistry":
        proposals = _replace_by_key(self.proposals, proposal, lambda item: item.proposal_hash)
        return RecoveryArtifactRegistry(
            proposals=proposals,
            simulations=self.simulations,
            handoffs=self.handoffs,
        )

    def register_simulation(self, simulation_report: RecoverySimulationReport) -> "RecoveryArtifactRegistry":
        simulations = _replace_by_key(self.simulations, simulation_report, lambda item: item.simulation_hash)
        return RecoveryArtifactRegistry(
            proposals=self.proposals,
            simulations=simulations,
            handoffs=self.handoffs,
        )

    def register_handoff(self, handoff_decision: RecoveryHandoffDecision) -> "RecoveryArtifactRegistry":
        handoffs = _replace_by_key(self.handoffs, handoff_decision, lambda item: item.decision_hash)
        return RecoveryArtifactRegistry(
            proposals=self.proposals,
            simulations=self.simulations,
            handoffs=handoffs,
        )


class RecoveryObservabilityService:
    def __init__(self, registry: RecoveryArtifactRegistry):
        self.registry = registry

    def get_recovery_timeline(self, proposal_hash: str) -> RecoveryTimeline:
        proposal = self._proposal_by_hash(proposal_hash)
        if proposal is None:
            return RecoveryTimeline(proposal_hash=proposal_hash, events=())

        events = [
            RecoveryTimelineEvent(
                sequence=SIGNAL_DETECTED,
                event_type=EVENT_SIGNAL,
                proposal_hash=proposal.proposal_hash,
                artifact_hash=proposal.proposal_hash,
                detail_code=proposal.signal.signal_type,
            ),
            RecoveryTimelineEvent(
                sequence=CLASSIFIED,
                event_type=EVENT_CLASSIFICATION,
                proposal_hash=proposal.proposal_hash,
                artifact_hash=proposal.proposal_hash,
                detail_code=proposal.diagnosis.classification,
            ),
            RecoveryTimelineEvent(
                sequence=PLAN_BUILT,
                event_type=EVENT_PLAN,
                proposal_hash=proposal.proposal_hash,
                artifact_hash=proposal.proposal_hash,
                detail_code=f"PLAN_STEPS:{len(proposal.plan.steps)}",
            ),
        ]

        simulation = self._simulation_by_proposal_hash(proposal.proposal_hash)
        if simulation is not None:
            events.append(
                RecoveryTimelineEvent(
                    sequence=SIMULATION_COMPLETED,
                    event_type=EVENT_SIMULATION,
                    proposal_hash=proposal.proposal_hash,
                    artifact_hash=simulation.simulation_hash,
                    detail_code=simulation.overall_risk,
                )
            )

        handoff = self._handoff_by_proposal_hash(proposal.proposal_hash)
        if handoff is not None:
            events.extend([
                RecoveryTimelineEvent(
                    sequence=AUTHORITY_HANDOFF,
                    event_type=EVENT_HANDOFF,
                    proposal_hash=proposal.proposal_hash,
                    artifact_hash=handoff.decision_hash,
                    detail_code=handoff.authority_name,
                ),
                RecoveryTimelineEvent(
                    sequence=AUTHORITY_DECISION,
                    event_type=EVENT_DECISION,
                    proposal_hash=proposal.proposal_hash,
                    artifact_hash=handoff.decision_hash,
                    detail_code=handoff.decision,
                ),
            ])

        return RecoveryTimeline(proposal_hash=proposal.proposal_hash, events=tuple(events))

    def get_recovery_decision(self, proposal_hash: str) -> Optional[RecoveryHandoffDecision]:
        return self._handoff_by_proposal_hash(proposal_hash)

    def get_recovery_analytics(self) -> RecoveryAnalyticsSnapshot:
        return RecoveryAnalyticsSnapshot(
            total_proposals=len(self.registry.proposals),
            approved_count=sum(1 for item in self.registry.handoffs if item.decision == RecoveryAuthorityDecision.APPROVED.value),
            rejected_count=sum(1 for item in self.registry.handoffs if item.decision == RecoveryAuthorityDecision.REJECTED.value),
            deferred_count=sum(1 for item in self.registry.handoffs if item.decision == RecoveryAuthorityDecision.DEFERRED.value),
            blocked_simulations=sum(1 for item in self.registry.simulations if item.overall_risk == RecoverySimulationRiskLevel.BLOCKED.value),
            high_risk_count=sum(1 for item in self.registry.simulations if item.overall_risk == RecoverySimulationRiskLevel.HIGH.value),
            medium_risk_count=sum(1 for item in self.registry.simulations if item.overall_risk == RecoverySimulationRiskLevel.MEDIUM.value),
            low_risk_count=sum(1 for item in self.registry.simulations if item.overall_risk == RecoverySimulationRiskLevel.LOW.value),
        )

    def list_recovery_proposals(self) -> Tuple[str, ...]:
        return tuple(item.proposal_hash for item in self.registry.proposals)

    def list_blocked_recoveries(self) -> Tuple[str, ...]:
        blocked = set()
        for item in self.registry.simulations:
            if item.overall_risk == RecoverySimulationRiskLevel.BLOCKED.value:
                blocked.add(item.proposal_hash)
        for item in self.registry.handoffs:
            if item.decision == RecoveryAuthorityDecision.REJECTED.value and item.blocked_reason_codes:
                blocked.add(item.proposal_hash)
        return tuple(sorted(blocked))

    def _proposal_by_hash(self, proposal_hash: str) -> Optional[RecoveryProposal]:
        for item in self.registry.proposals:
            if item.proposal_hash == proposal_hash:
                return item
        return None

    def _simulation_by_proposal_hash(self, proposal_hash: str) -> Optional[RecoverySimulationReport]:
        matches = [item for item in self.registry.simulations if item.proposal_hash == proposal_hash]
        return matches[0] if matches else None

    def _handoff_by_proposal_hash(self, proposal_hash: str) -> Optional[RecoveryHandoffDecision]:
        matches = [item for item in self.registry.handoffs if item.proposal_hash == proposal_hash]
        return matches[0] if matches else None


def _replace_by_key(items, new_item, key_func):
    key = key_func(new_item)
    filtered = tuple(item for item in items if key_func(item) != key)
    return filtered + (new_item,)


def _sort_proposals(items: Tuple[RecoveryProposal, ...]) -> Tuple[RecoveryProposal, ...]:
    return tuple(sorted(items, key=lambda item: item.proposal_hash))


def _sort_simulations(items: Tuple[RecoverySimulationReport, ...]) -> Tuple[RecoverySimulationReport, ...]:
    return tuple(sorted(items, key=lambda item: (item.proposal_hash, item.simulation_hash)))


def _sort_handoffs(items: Tuple[RecoveryHandoffDecision, ...]) -> Tuple[RecoveryHandoffDecision, ...]:
    return tuple(sorted(items, key=lambda item: (item.proposal_hash, item.simulation_hash, item.decision_hash)))
