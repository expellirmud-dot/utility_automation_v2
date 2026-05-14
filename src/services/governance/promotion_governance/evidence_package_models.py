"""
Frozen immutable models for the Governance Evidence Package.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
- Reference-based bundling (hashes only)
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Tuple, Literal


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


PackageStatus = Literal[
    "PACKAGE_VERIFIED",
    "PACKAGE_INVALID",
]


@dataclass(frozen=True)
class GovernanceEvidencePackage:
    """
    Deterministic evidence package that bundles references to the governance chain.
    
    This is an audit/reference artifact only.
    No runtime execution authority.
    """
    package_id: str
    package_version: str
    archive_hash: str
    human_record_hash: str
    evidence_link_hash: str
    package_status: PackageStatus
    reason_codes: Tuple[str, ...]

    def __post_init__(self) -> None:
        # Structural validation - Raise for invalid inputs
        if not self.package_id:
            raise ValueError("package_id is required")
        if not self.archive_hash:
            raise ValueError("archive_hash is required")
        if not self.human_record_hash:
            raise ValueError("human_record_hash is required")
        if not self.evidence_link_hash:
            raise ValueError("evidence_link_hash is required")
        
        valid_statuses = {"PACKAGE_VERIFIED", "PACKAGE_INVALID"}
        if self.package_status not in valid_statuses:
            raise ValueError(f"Invalid package_status: {self.package_status}. Must be one of {valid_statuses}")

        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted canonically")

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic package hash (excludes package_hash itself)."""
        return {
            "archive_hash": self.archive_hash,
            "evidence_link_hash": self.evidence_link_hash,
            "human_record_hash": self.human_record_hash,
            "package_id": self.package_id,
            "package_status": self.package_status,
            "package_version": self.package_version,
            "reason_codes": self.reason_codes,
        }

    @property
    def package_hash(self) -> str:
        """Deterministic SHA256 hash of the package identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "package_hash": self.package_hash,
        }
