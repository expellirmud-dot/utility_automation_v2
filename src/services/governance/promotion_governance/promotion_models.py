"""
Frozen immutable domain models for promotion governance.

Requirements:
- deterministic serialization
- canonical ordering
- no timestamps in identity hash
- full auditability
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Tuple


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class PromotionEligibilityFailure:
    """Single eligibility criterion failure."""
    criterion_key: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "criterion_key": self.criterion_key,
            "detail": self.detail,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PromotionEligibilityCriterion:
    """Single promotion eligibility criterion."""
    key: str
    category: str
    description: str
    stable_order: int
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "description": self.description,
            "key": self.key,
            "required": self.required,
            "stable_order": self.stable_order,
        }


@dataclass(frozen=True)
class PromotionEligibilityResult:
    """Result of evaluating a single eligibility criterion."""
    criterion: PromotionEligibilityCriterion
    satisfied: bool
    failure: PromotionEligibilityFailure | None = None

    def __post_init__(self) -> None:
        if not self.satisfied and self.failure is None:
            raise ValueError("failed eligibility result requires a failure")

    def to_dict(self) -> dict[str, object]:
        return {
            "criterion": self.criterion.to_dict(),
            "failure": self.failure.to_dict() if self.failure else None,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class PromotionEligibility:
    """
    Deterministic promotion eligibility assessment.
    
    No timestamps in identity hash.
    No execution authority.
    Governance visibility only.
    """
    results: Tuple[PromotionEligibilityResult, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)
    artifact_version: str = "task-050-b-promotion-governance-v1"

    def __post_init__(self) -> None:
        # Enforce canonical ordering
        ordered = tuple(sorted(self.results, key=lambda item: item.criterion.stable_order))
        if ordered != self.results:
            raise ValueError("promotion eligibility results must be in canonical order")

    @property
    def eligible(self) -> bool:
        """Release is eligible if all required criteria are satisfied."""
        return all(
            result.satisfied
            for result in self.results
            if result.criterion.required
        )

    @property
    def eligibility_score(self) -> float:
        """Percentage of satisfied criteria."""
        if not self.results:
            return 0.0
        satisfied_count = sum(1 for result in self.results if result.satisfied)
        return (satisfied_count / len(self.results)) * 100

    @property
    def failures(self) -> Tuple[PromotionEligibilityFailure, ...]:
        """All eligibility failures."""
        return tuple(
            result.failure
            for result in self.results
            if result.failure is not None
        )

    def identity_payload(self) -> dict[str, object]:
        """Payload for identity hash (excludes metadata, no timestamps)."""
        return {
            "artifact_version": self.artifact_version,
            "eligible": self.eligible,
            "eligibility_score": self.eligibility_score,
            "results": [result.to_dict() for result in self.results],
        }

    @property
    def eligibility_hash(self) -> str:
        """Deterministic hash of eligibility assessment."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "eligibility_hash": self.eligibility_hash,
            "metadata": dict(sorted(self.metadata.items())),
        }


@dataclass(frozen=True)
class PromotionRequest:
    """
    Request to promote a release to a new stage.
    
    No execution authority.
    Governance visibility only.
    """
    source_version_id: str
    target_stage: str  # e.g., "simulation", "approved", "production"
    requested_by: str  # Actor identifier
    request_epoch: int  # Deterministic epoch counter
    request_seq: int  # Sequence in epoch
    governance_evidence: Mapping[str, str] = field(default_factory=dict)  # Evidence hashes

    def __post_init__(self) -> None:
        # Validate stage
        valid_stages = {"simulation", "approved", "production"}
        if self.target_stage not in valid_stages:
            raise ValueError(f"Invalid target_stage: {self.target_stage}")

    def to_dict(self) -> dict[str, object]:
        return {
            "governance_evidence": dict(sorted(self.governance_evidence.items())),
            "request_epoch": self.request_epoch,
            "request_seq": self.request_seq,
            "requested_by": self.requested_by,
            "source_version_id": self.source_version_id,
            "target_stage": self.target_stage,
        }


@dataclass(frozen=True)
class PromotionDecision:
    """
    Governance decision on promotion eligibility.
    
    No execution authority.
    Decision only - no runtime changes.
    """
    promotion_request: PromotionRequest
    eligibility: PromotionEligibility
    decision: str  # "approved", "deferred", "rejected"
    decision_rationale: str
    decision_epoch: int
    decision_seq: int

    def __post_init__(self) -> None:
        valid_decisions = {"approved", "deferred", "rejected"}
        if self.decision not in valid_decisions:
            raise ValueError(f"Invalid decision: {self.decision}")

    def identity_payload(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "decision_epoch": self.decision_epoch,
            "decision_seq": self.decision_seq,
            "decision_rationale": self.decision_rationale,
            "eligibility": self.eligibility.identity_payload(),
            "promotion_request": self.promotion_request.to_dict(),
        }

    @property
    def decision_hash(self) -> str:
        """Deterministic hash of governance decision."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "decision_hash": self.decision_hash,
        }


@dataclass(frozen=True)
class PromotionBundle:
    """
    Complete governance promotion bundle.
    
    Packages all promotion governance information.
    No execution authority.
    Deterministic and hashable.
    """
    request: PromotionRequest
    eligibility: PromotionEligibility
    decision: PromotionDecision
    bundle_version: str = "task-050-b-promotion-governance-bundle-v1"
    additional_metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate consistency
        if self.decision.promotion_request != self.request:
            raise ValueError("decision request must match promotion request")
        if self.decision.eligibility != self.eligibility:
            raise ValueError("decision eligibility must match promotion eligibility")

    def identity_payload(self) -> dict[str, object]:
        """Payload for bundle identity hash."""
        return {
            "bundle_version": self.bundle_version,
            "decision": self.decision.identity_payload(),
            "eligibility": self.eligibility.identity_payload(),
            "request": self.request.to_dict(),
        }

    @property
    def bundle_hash(self) -> str:
        """Deterministic hash of entire promotion bundle."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "additional_metadata": dict(sorted(self.additional_metadata.items())),
            "bundle_hash": self.bundle_hash,
        }
