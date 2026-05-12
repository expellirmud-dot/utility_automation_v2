from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, Tuple

from src.services.governance.recovery.recovery_models import RecoveryProposal
from src.services.governance.recovery.recovery_report_hasher import (
    compute_proposal_hash,
    stable_hash,
)
from src.services.governance.recovery.recovery_simulation_gate import (
    RecoverySimulationReport,
    RecoverySimulationRiskLevel,
)


LOCAL_VALIDATOR_AUTHORITY = "LOCAL_RECOVERY_HANDOFF_VALIDATOR"
UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"

BLOCKED_INVALID_PROPOSAL_HASH = "BLOCKED_INVALID_PROPOSAL_HASH"
BLOCKED_INVALID_SIMULATION_HASH = "BLOCKED_INVALID_SIMULATION_HASH"
BLOCKED_PROPOSAL_SIMULATION_MISMATCH = "BLOCKED_PROPOSAL_SIMULATION_MISMATCH"
BLOCKED_SIMULATION_NOT_READY = "BLOCKED_SIMULATION_NOT_READY"
BLOCKED_SIMULATION_RISK = "BLOCKED_SIMULATION_RISK"
BLOCKED_INVALID_AUTHORITY_DECISION = "BLOCKED_INVALID_AUTHORITY_DECISION"


class RecoveryAuthorityDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class RecoveryAuthorityResponse:
    decision: str
    decision_reason: str = ""
    authority_name: Optional[str] = None

    def normalized_authority_name(self) -> str:
        return _normalize_authority_name(self.authority_name)

    def normalized_decision_reason(self) -> str:
        return _normalize_text(self.decision_reason)


@dataclass(frozen=True)
class RecoveryHandoffRequest:
    proposal: RecoveryProposal
    simulation_report: RecoverySimulationReport
    request_hash: str = field(default="")

    def __post_init__(self):
        if not self.request_hash:
            object.__setattr__(self, "request_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "proposal_hash": self.proposal.proposal_hash,
            "simulation_hash": self.simulation_report.simulation_hash,
        }
        if include_hash:
            payload["request_hash"] = self.request_hash
        return payload


@dataclass(frozen=True)
class RecoveryHandoffDecision:
    decision: str
    decision_reason: str
    proposal_hash: str
    simulation_hash: str
    authority_name: str
    authority_response_hash: str
    ready_for_execution: bool
    blocked_reason_codes: Tuple[str, ...] = ()
    decision_hash: str = field(default="")

    def __post_init__(self):
        if self.decision not in {item.value for item in RecoveryAuthorityDecision}:
            raise ValueError(f"Invalid authority decision: {self.decision}")
        object.__setattr__(self, "blocked_reason_codes", tuple(sorted(self.blocked_reason_codes)))
        if self.ready_for_execution and self.decision != RecoveryAuthorityDecision.APPROVED.value:
            raise ValueError("ready_for_execution requires APPROVED decision")
        if not self.decision_hash:
            object.__setattr__(self, "decision_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "authority_name": self.authority_name,
            "authority_response_hash": self.authority_response_hash,
            "blocked_reason_codes": list(self.blocked_reason_codes),
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "proposal_hash": self.proposal_hash,
            "ready_for_execution": self.ready_for_execution,
            "simulation_hash": self.simulation_hash,
        }
        if include_hash:
            payload["decision_hash"] = self.decision_hash
        return payload


class MeshAuthorityAdapter(Protocol):
    def evaluate_recovery_proposal(self, request: RecoveryHandoffRequest) -> RecoveryAuthorityResponse:
        ...


class RecoveryProposalHandoff:
    def handoff_proposal(
        self,
        proposal: RecoveryProposal,
        simulation_report: RecoverySimulationReport,
        authority_adapter: MeshAuthorityAdapter,
    ) -> RecoveryHandoffDecision:
        blocked_reason_codes = self._validate_before_handoff(proposal, simulation_report)
        if blocked_reason_codes:
            return self._blocked_decision(
                proposal_hash=proposal.proposal_hash,
                simulation_hash=simulation_report.simulation_hash,
                blocked_reason_codes=blocked_reason_codes,
            )

        request = RecoveryHandoffRequest(proposal=proposal, simulation_report=simulation_report)
        response = authority_adapter.evaluate_recovery_proposal(request)
        normalized_name = _normalize_authority_name(getattr(response, "authority_name", None))
        normalized_reason = _normalize_text(getattr(response, "decision_reason", ""))
        normalized_decision = self._normalize_decision(getattr(response, "decision", ""))

        if normalized_decision is None:
            return self._blocked_decision(
                proposal_hash=proposal.proposal_hash,
                simulation_hash=simulation_report.simulation_hash,
                blocked_reason_codes=(BLOCKED_INVALID_AUTHORITY_DECISION,),
                authority_name=normalized_name,
                decision_reason=BLOCKED_INVALID_AUTHORITY_DECISION,
            )

        authority_response_hash = _authority_response_hash(
            decision=normalized_decision.value,
            decision_reason=normalized_reason,
            authority_name=normalized_name,
        )
        return RecoveryHandoffDecision(
            decision=normalized_decision.value,
            decision_reason=normalized_reason,
            proposal_hash=proposal.proposal_hash,
            simulation_hash=simulation_report.simulation_hash,
            authority_name=normalized_name,
            authority_response_hash=authority_response_hash,
            ready_for_execution=normalized_decision == RecoveryAuthorityDecision.APPROVED,
        )

    def _validate_before_handoff(
        self,
        proposal: RecoveryProposal,
        simulation_report: RecoverySimulationReport,
    ) -> Tuple[str, ...]:
        blocked_reason_codes = []
        if proposal.proposal_hash != compute_proposal_hash(proposal):
            blocked_reason_codes.append(BLOCKED_INVALID_PROPOSAL_HASH)
        if simulation_report.simulation_hash != stable_hash(simulation_report.to_hash_payload()):
            blocked_reason_codes.append(BLOCKED_INVALID_SIMULATION_HASH)
        if simulation_report.proposal_hash != proposal.proposal_hash:
            blocked_reason_codes.append(BLOCKED_PROPOSAL_SIMULATION_MISMATCH)
        if simulation_report.ready_for_handoff is False:
            blocked_reason_codes.append(BLOCKED_SIMULATION_NOT_READY)
        if simulation_report.overall_risk == RecoverySimulationRiskLevel.BLOCKED.value:
            blocked_reason_codes.append(BLOCKED_SIMULATION_RISK)
        return tuple(sorted(blocked_reason_codes))

    def _blocked_decision(
        self,
        proposal_hash: str,
        simulation_hash: str,
        blocked_reason_codes: Tuple[str, ...],
        authority_name: str = LOCAL_VALIDATOR_AUTHORITY,
        decision_reason: str = "",
    ) -> RecoveryHandoffDecision:
        sorted_codes = tuple(sorted(blocked_reason_codes))
        reason = decision_reason or "HANDOFF_REJECTED:" + "|".join(sorted_codes)
        normalized_name = _normalize_authority_name(authority_name)
        authority_response_hash = _authority_response_hash(
            decision=RecoveryAuthorityDecision.REJECTED.value,
            decision_reason=reason,
            authority_name=normalized_name,
        )
        return RecoveryHandoffDecision(
            decision=RecoveryAuthorityDecision.REJECTED.value,
            decision_reason=reason,
            proposal_hash=proposal_hash,
            simulation_hash=simulation_hash,
            authority_name=normalized_name,
            authority_response_hash=authority_response_hash,
            ready_for_execution=False,
            blocked_reason_codes=sorted_codes,
        )

    @staticmethod
    def _normalize_decision(decision: object) -> Optional[RecoveryAuthorityDecision]:
        normalized = _normalize_text(decision).upper()
        try:
            return RecoveryAuthorityDecision(normalized)
        except ValueError:
            return None


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_authority_name(value: object) -> str:
    normalized = _normalize_text(value)
    return normalized if normalized else UNKNOWN_AUTHORITY


def _authority_response_hash(decision: str, decision_reason: str, authority_name: str) -> str:
    return stable_hash({
        "authority_name": authority_name,
        "decision": decision,
        "decision_reason": decision_reason,
    })
