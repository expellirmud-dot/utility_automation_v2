"""
Frozen immutable models for the Human Authorization Record.

Requirements:
- Deterministic serialization
- Canonical ordering
- No timestamps in identity hash
- Full auditability
- Record of intent only, no execution authority
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Tuple, Literal


def canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


ReviewIntent = Literal[
    "REVIEW_INTENT_APPROVE",
    "REVIEW_INTENT_REJECT",
    "REVIEW_INTENT_DEFER",
]


@dataclass(frozen=True)
class HumanAuthorizationRecord:
    """
    Deterministic record of human review intent.
    
    This is a record of intent only.
    It does NOT grant runtime execution authority.
    """
    archive_hash: str
    authorizer_id: str
    review_intent: ReviewIntent
    rationale: str
    authorization_epoch: int
    authorization_seq: int
    record_version: str = "task-053-human-auth-v1"

    def __post_init__(self) -> None:
        if not self.archive_hash:
            raise ValueError("archive_hash is required")
        if not self.authorizer_id:
            raise ValueError("authorizer_id is required")
        
        valid_intents = {"REVIEW_INTENT_APPROVE", "REVIEW_INTENT_REJECT", "REVIEW_INTENT_DEFER"}
        if self.review_intent not in valid_intents:
            raise ValueError(f"Invalid review_intent: {self.review_intent}. Must be one of {valid_intents}")
            
        if self.authorization_epoch < 0:
            raise ValueError("authorization_epoch must be >= 0")
        if self.authorization_seq < 0:
            raise ValueError("authorization_seq must be >= 0")

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic record hash (excludes record_hash itself)."""
        return {
            "archive_hash": self.archive_hash,
            "authorizer_id": self.authorizer_id,
            "authorization_epoch": self.authorization_epoch,
            "authorization_seq": self.authorization_seq,
            "rationale": self.rationale,
            "record_version": self.record_version,
            "review_intent": self.review_intent,
        }

    @property
    def record_hash(self) -> str:
        """Deterministic SHA256 hash of the record identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "record_hash": self.record_hash,
        }


@dataclass(frozen=True)
class HumanAuthorizationSummary:
    """
    Lightweight deterministic projection of a human authorization record.
    """
    archive_hash: str
    authorizer_id: str
    review_intent: ReviewIntent
    authorization_epoch: int
    authorization_seq: int
    record_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_hash": self.archive_hash,
            "authorizer_id": self.authorizer_id,
            "authorization_epoch": self.authorization_epoch,
            "authorization_seq": self.authorization_seq,
            "record_hash": self.record_hash,
            "review_intent": self.review_intent,
        }
