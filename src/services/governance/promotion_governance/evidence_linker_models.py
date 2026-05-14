"""
Frozen immutable models for the Human Review Intent Evidence Linker.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
- Explicit recording of both archive hashes for auditability
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Tuple, Literal


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


LinkStatus = Literal[
    "LINK_VERIFIED",
    "LINK_BLOCKED_ARCHIVE_MISMATCH",
]


@dataclass(frozen=True)
class HumanReviewEvidenceLink:
    """
    Deterministic evidence link between a Human Authorization Record and a Release Governance Archive.
    
    Used to verify that the human record was intended for the specific archive version.
    """
    archive_hash: str
    record_archive_hash: str
    record_hash: str
    link_status: LinkStatus
    reason_codes: Tuple[str, ...]
    link_version: str = "task-055-evidence-link-v1"

    def __post_init__(self) -> None:
        # Enforce canonical ordering of reason codes
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted canonically")
        
        if self.link_status not in {"LINK_VERIFIED", "LINK_BLOCKED_ARCHIVE_MISMATCH"}:
            raise ValueError(f"Invalid link_status: {self.link_status}")

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic link hash (excludes link_hash itself)."""
        return {
            "archive_hash": self.archive_hash,
            "link_status": self.link_status,
            "link_version": self.link_version,
            "reason_codes": self.reason_codes,
            "record_archive_hash": self.record_archive_hash,
            "record_hash": self.record_hash,
        }

    @property
    def link_hash(self) -> str:
        """Deterministic SHA256 hash of the link identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "link_hash": self.link_hash,
        }
