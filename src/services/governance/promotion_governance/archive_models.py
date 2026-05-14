"""
Frozen immutable models for the Release Governance Artifact Archive.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
- Evidence-based referencing instead of full object nesting
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Tuple, Optional


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class ReleaseGovernanceEvidenceRef:
    """
    Reference to a specific artifact in the governance chain.
    
    Used to build a deterministic evidence chain without nesting full objects.
    """
    stage: str
    artifact_type: str
    artifact_hash: str
    advisory_decision: Optional[str] = None
    passed: Optional[bool] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "advisory_decision": self.advisory_decision,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ReleaseGovernanceArchive:
    """
    Deterministic archive of the release governance evidence chain.
    
    No execution authority.
    No timestamps in identity hash.
    Deterministic and hashable.
    """
    release_id: str
    certification_artifact_hash: str
    gatekeeper_report_hash: str
    authorization_hash: str
    advisory_decision: str
    passed: bool
    reason_codes: Tuple[str, ...]
    evidence_chain: Tuple[ReleaseGovernanceEvidenceRef, ...]
    promotion_bundle_hash: Optional[str] = None
    archive_version: str = "task-052-archive-v1"

    def __post_init__(self) -> None:
        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted canonically")
        
        # Enforce stable stage order for evidence chain
        # 10 certification, 20 gatekeeper, 30 promotion, 40 authorization
        stage_order = {
            "certification": 10,
            "gatekeeper": 20,
            "promotion_governance": 30,
            "release_authorization": 40,
        }
        
        def get_order(ref: ReleaseGovernanceEvidenceRef) -> int:
            return stage_order.get(ref.stage, 999)
        
        ordered_chain = tuple(sorted(self.evidence_chain, key=get_order))
        if ordered_chain != self.evidence_chain:
            raise ValueError("evidence_chain must be sorted by stable stage order")

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic archive hash (excludes archive_hash itself)."""
        return {
            "advisory_decision": self.advisory_decision,
            "archive_version": self.archive_version,
            "authorization_hash": self.authorization_hash,
            "certification_artifact_hash": self.certification_artifact_hash,
            "evidence_chain": [ref.to_dict() for ref in self.evidence_chain],
            "gatekeeper_report_hash": self.gatekeeper_report_hash,
            "passed": self.passed,
            "promotion_bundle_hash": self.promotion_bundle_hash,
            "reason_codes": self.reason_codes,
            "release_id": self.release_id,
        }

    @property
    def archive_hash(self) -> str:
        """Deterministic SHA256 hash of the archive identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "archive_hash": self.archive_hash,
        }
