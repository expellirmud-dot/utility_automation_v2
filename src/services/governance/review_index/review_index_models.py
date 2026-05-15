"""
Frozen immutable models for the Governance Review Index.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
- Advisory only: consolidates governance hashes into a single index artifact
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Tuple, Literal


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


IndexStatus = Literal[
    "INDEX_READY",
    "INDEX_BLOCKED_MISSING_REFERENCE",
    "INDEX_BLOCKED_INTEGRITY_FAILED",
    "INDEX_BLOCKED_READINESS_FAILED",
]


@dataclass(frozen=True)
class GovernanceReviewIndexBundle:
    """
    A deterministic audit index that bundles references to the full governance review chain.
    
    This is the final consolidation artifact for a specific governance review.
    No runtime execution authority.
    """
    index_version: str
    index_status: IndexStatus
    certification_artifact_hash: str
    promotion_governance_hash: str
    evidence_package_hash: str
    integrity_report_hash: str
    readiness_report_hash: str
    review_summary_hash: str
    readiness_decision: str
    integrity_passed: bool
    invariant_keys: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    index_hash: str

    def __post_init__(self) -> None:
        # Structural validation
        if not self.index_version:
            raise ValueError("index_version is required")
        
        valid_statuses = {"INDEX_READY", "INDEX_BLOCKED_MISSING_REFERENCE", "INDEX_BLOCKED_INTEGRITY_FAILED", "INDEX_BLOCKED_READINESS_FAILED"}
        if self.index_status not in valid_statuses:
            raise ValueError(f"Invalid index_status: {self.index_status}. Must be one of {valid_statuses}")
        
        # Enforce canonical ordering of invariant keys
        if tuple(sorted(self.invariant_keys)) != self.invariant_keys:
            raise ValueError("invariant_keys must be sorted canonically")
            
        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted canonically")

        # Validate index_hash matches deterministic recomputation
        if self.index_hash != self._compute_hash():
            raise ValueError("index_hash mismatch: provided hash does not match recomputed identity hash")

    def _compute_hash(self) -> str:
        """Deterministic SHA256 hash of the index identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic index hash (excludes index_hash itself)."""
        return {
            "certification_artifact_hash": self.certification_artifact_hash,
            "evidence_package_hash": self.evidence_package_hash,
            "index_status": self.index_status,
            "index_version": self.index_version,
            "integrity_passed": self.integrity_passed,
            "integrity_report_hash": self.integrity_report_hash,
            "invariant_keys": self.invariant_keys,
            "promotion_governance_hash": self.promotion_governance_hash,
            "readiness_decision": self.readiness_decision,
            "readiness_report_hash": self.readiness_report_hash,
            "reason_codes": self.reason_codes,
            "review_summary_hash": self.review_summary_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "index_hash": self.index_hash,
        }

