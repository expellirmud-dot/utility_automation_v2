"""
Read-only provider for Human Review Intent projection data.

Requirements:
- Deterministic projection of human review intent records
- No storage retrieval or persistence
- No write operations
- No mesh/quorum calls
- No src.tests.* imports
"""

from __future__ import annotations

from typing import Any, List, Dict
from src.services.governance.promotion_governance.human_auth_models import (
    HumanAuthorizationRecord,
    HumanAuthorizationSummary,
)

class HumanReviewIntentProvider:
    """
    Provides read-only projection data for human review intent records.
    
    Note: In this phase, data is provided as deterministic projections
    to avoid premature storage implementation.
    """

    @staticmethod
    def get_latest_review_records() -> List[Dict[str, Any]]:
        """
        Returns a deterministic list of human review intent records.
        
        This is a read-only projection.
        """
        # Deterministic sample data for projection/demo purposes
        # In a real system, this would be a read-only projection from the ledger/cache.
        
        # Record 1: Approved intent
        rec1 = HumanAuthorizationRecord(
            archive_hash="arch-hash-stable-001",
            authorizer_id="gov-officer-01",
            review_intent="REVIEW_INTENT_APPROVE",
            rationale="Certification artifacts verified and align with policy P-101.",
            authorization_epoch=1,
            authorization_seq=0,
        )

        # Record 2: Deferred intent
        rec2 = HumanAuthorizationRecord(
            archive_hash="arch-hash-stable-002",
            authorizer_id="gov-officer-02",
            review_intent="REVIEW_INTENT_DEFER",
            rationale="Awaiting additional security scan results for dependency v2.1.0.",
            authorization_epoch=1,
            authorization_seq=1,
        )

        # Record 3: Rejected intent
        rec3 = HumanAuthorizationRecord(
            archive_hash="arch-hash-stable-003",
            authorizer_id="gov-officer-01",
            review_intent="REVIEW_INTENT_REJECT",
            rationale="Critical failure in deterministic certifier check 'mesh_determinism'.",
            authorization_epoch=1,
            authorization_seq=2,
        )

        return [rec.to_dict() for rec in [rec1, rec2, rec3]]

    @staticmethod
    def get_record_by_archive_hash(archive_hash: str) -> Dict[str, Any] | None:
        """
        Returns a specific review record based on the archive hash.
        """
        records = HumanReviewIntentProvider.get_latest_review_records()
        for rec in records:
            if rec["archive_hash"] == archive_hash:
                return rec
        return None
