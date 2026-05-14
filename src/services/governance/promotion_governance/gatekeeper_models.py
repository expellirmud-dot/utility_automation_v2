"""
Frozen immutable models for the Promotion Gatekeeper.
Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Tuple, Literal

GatekeeperDecision = Literal[
    "ELIGIBLE_FOR_PROMOTION_REVIEW",
    "BLOCKED_CERTIFICATION_FAILED",
    "BLOCKED_REQUIRED_CHECK_MISSING",
    "BLOCKED_REQUIRED_CHECK_FAILED",
]

def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

@dataclass(frozen=True)
class GatekeeperCheckResult:
    """Result of a specific gatekeeper check evaluation."""
    check_key: str
    satisfied: bool
    reason: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "check_key": self.check_key,
            "detail": self.detail,
            "reason": self.reason,
            "satisfied": self.satisfied,
        }

@dataclass(frozen=True)
class PromotionGatekeeperReport:
    """
    Deterministic report produced by the Promotion Gatekeeper.
    
    No execution authority. Advisory only.
    """
    passed: bool
    required_results: Tuple[GatekeeperCheckResult, ...]
    missing_required_checks: Tuple[str, ...]
    failed_required_checks: Tuple[str, ...]
    unknown_checks: Tuple[str, ...]
    advisory_decision: GatekeeperDecision
    reason_codes: Tuple[str, ...]
    source_certification_hash: str
    report_version: str = "task-051-a-gatekeeper-v1"
    additional_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Enforce canonical ordering of results
        ordered_results = tuple(sorted(self.required_results, key=lambda r: r.check_key))
        if ordered_results != self.required_results:
            raise ValueError("required_results must be in canonical order (sorted by check_key)")
        
        if tuple(sorted(self.missing_required_checks)) != self.missing_required_checks:
            raise ValueError("missing_required_checks must be sorted")
            
        if tuple(sorted(self.failed_required_checks)) != self.failed_required_checks:
            raise ValueError("failed_required_checks must be sorted")
            
        if tuple(sorted(self.unknown_checks)) != self.unknown_checks:
            raise ValueError("unknown_checks must be sorted")
            
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted")

    def identity_payload(self) -> dict[str, object]:
        """Payload for deterministic report hash."""
        return {
            "advisory_decision": self.advisory_decision,
            "failed_required_checks": self.failed_required_checks,
            "missing_required_checks": self.missing_required_checks,
            "passed": self.passed,
            "reason_codes": self.reason_codes,
            "report_version": self.report_version,
            "required_results": [r.to_dict() for r in self.required_results],
            "source_certification_hash": self.source_certification_hash,
            "unknown_checks": self.unknown_checks,
        }

    @property
    def report_hash(self) -> str:
        """Deterministic hash of the report content."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Full deterministic dictionary representation."""
        return {
            **self.identity_payload(),
            "additional_metadata": dict(sorted(self.additional_metadata.items())),
            "report_hash": self.report_hash,
        }
