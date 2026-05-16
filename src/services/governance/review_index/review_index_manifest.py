"""
Deterministic export manifest for the Governance Review Index.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Advisory only: provides a compact audit manifest of the index bundle
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Tuple

from src.services.governance.review_index.review_index_models import (
    GovernanceReviewIndexBundle,
    canonical_json,
)


@dataclass(frozen=True)
class GovernanceReviewIndexManifest:
    """
    A deterministic export manifest representing a Governance Review Index Bundle.
    
    This manifest is a compact representation used for audit exports.
    No runtime execution authority.
    """
    manifest_version: str
    index_hash: str
    index_status: str
    readiness_decision: str
    integrity_passed: bool
    evidence_package_hash: str
    review_summary_hash: str
    certification_artifact_hash: str
    promotion_governance_hash: str
    invariant_keys: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    manifest_hash: str

    def __post_init__(self) -> None:
        # Enforce canonical ordering of invariant keys
        if tuple(sorted(self.invariant_keys)) != self.invariant_keys:
            raise ValueError("invariant_keys must be sorted canonically")
            
        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted canonically")

        # Validate manifest_hash matches deterministic recomputation
        if self.manifest_hash != self._compute_hash():
            raise ValueError("manifest_hash mismatch: provided hash does not match recomputed identity hash")

    def _compute_hash(self) -> str:
        """Deterministic SHA256 hash of the manifest identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic manifest hash (excludes manifest_hash itself)."""
        return {
            "certification_artifact_hash": self.certification_artifact_hash,
            "evidence_package_hash": self.evidence_package_hash,
            "index_hash": self.index_hash,
            "index_status": self.index_status,
            "integrity_passed": self.integrity_passed,
            "invariant_keys": self.invariant_keys,
            "manifest_version": self.manifest_version,
            "promotion_governance_hash": self.promotion_governance_hash,
            "readiness_decision": self.readiness_decision,
            "reason_codes": self.reason_codes,
            "review_summary_hash": self.review_summary_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "manifest_version": self.manifest_version,
            "manifest_hash": self.manifest_hash,
        }


class GovernanceReviewIndexManifestBuilder:
    """
    Builder for creating deterministic GovernanceReviewIndexManifest artifacts.
    """

    MANIFEST_VERSION = "task-070-review-index-manifest-v1"

    @classmethod
    def from_index(cls, index_bundle: GovernanceReviewIndexBundle) -> GovernanceReviewIndexManifest:
        """
        Creates a deterministic GovernanceReviewIndexManifest from a GovernanceReviewIndexBundle.
        
        Preserves blocked statuses and existing hashes without fabrication.
        """
        # 1. Ensure canonical ordering of reasons and invariants (already enforced by Bundle, but for safety)
        sorted_reasons = tuple(sorted(list(index_bundle.reason_codes)))
        sorted_invariants = tuple(sorted(list(index_bundle.invariant_keys)))

        # 2. Prepare identity payload for hash calculation
        identity_payload = {
            "certification_artifact_hash": index_bundle.certification_artifact_hash,
            "evidence_package_hash": index_bundle.evidence_package_hash,
            "index_hash": index_bundle.index_hash,
            "index_status": index_bundle.index_status,
            "integrity_passed": index_bundle.integrity_passed,
            "invariant_keys": sorted_invariants,
            "manifest_version": cls.MANIFEST_VERSION,
            "promotion_governance_hash": index_bundle.promotion_governance_hash,
            "readiness_decision": index_bundle.readiness_decision,
            "reason_codes": sorted_reasons,
            "review_summary_hash": index_bundle.review_summary_hash,
        }
        
        manifest_hash = hashlib.sha256(
            canonical_json(identity_payload).encode("utf-8")
        ).hexdigest()

        return GovernanceReviewIndexManifest(
            manifest_version=cls.MANIFEST_VERSION,
            index_hash=index_bundle.index_hash,
            index_status=index_bundle.index_status,
            readiness_decision=index_bundle.readiness_decision,
            integrity_passed=index_bundle.integrity_passed,
            evidence_package_hash=index_bundle.evidence_package_hash,
            review_summary_hash=index_bundle.review_summary_hash,
            certification_artifact_hash=index_bundle.certification_artifact_hash,
            promotion_governance_hash=index_bundle.promotion_governance_hash,
            invariant_keys=sorted_invariants,
            reason_codes=sorted_reasons,
            manifest_hash=manifest_hash,
        )
