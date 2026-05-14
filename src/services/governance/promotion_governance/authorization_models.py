"""
Frozen immutable models for Release Authorization.
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

# Advisory-only decisions to avoid implying runtime authority
ReleaseAuthorizationDecision = Literal[
    "ELIGIBLE_FOR_RELEASE_AUTHORIZATION_REVIEW",
    "BLOCKED_CERTIFICATION_FAILED",
    "BLOCKED_GATEKEEPER_FAILED",
    "BLOCKED_INPUT_INCONSISTENT",
]

def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

@dataclass(frozen=True)
class ReleaseAuthorizationBundle:
    """
    Deterministic authorization bundle for release review.
    
    No execution authority. Advisory only.
    """
    passed: bool
    advisory_decision: ReleaseAuthorizationDecision
    source_certification_hash: str
    source_gatekeeper_hash: str
    reason_codes: Tuple[str, ...]
    bundle_version: str = "task-051-b-auth-v1"
    additional_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted")

    def identity_payload(self) -> dict[str, object]:
        """Payload for deterministic bundle hash."""
        return {
            "advisory_decision": self.advisory_decision,
            "bundle_version": self.bundle_version,
            "passed": self.passed,
            "reason_codes": self.reason_codes,
            "source_certification_hash": self.source_certification_hash,
            "source_gatekeeper_hash": self.source_gatekeeper_hash,
        }

    @property
    def authorization_hash(self) -> str:
        """Deterministic hash of the authorization bundle."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Full deterministic dictionary representation."""
        return {
            **self.identity_payload(),
            "additional_metadata": dict(sorted(self.additional_metadata.items())),
            "authorization_hash": self.authorization_hash,
        }
