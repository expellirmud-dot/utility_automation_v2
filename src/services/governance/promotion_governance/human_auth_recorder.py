"""
Deterministic recorder for human review intent.

Requirements:
- Consume archive reference and review intent
- Produce deterministic HumanAuthorizationRecord
- No runtime execution authority
- No ledger mutation
- No mesh/quorum calls
- No src.tests.* imports
"""

from __future__ import annotations

from typing import Optional
from src.services.governance.promotion_governance.human_auth_models import (
    HumanAuthorizationRecord,
    HumanAuthorizationSummary,
)


class HumanAuthRecorder:
    """
    Deterministic recorder that documents human review intent.
    """

    @staticmethod
    def record_intent(
        archive_hash: str,
        authorizer_id: str,
        review_intent: str,
        rationale: str,
        authorization_epoch: int,
        authorization_seq: int,
    ) -> HumanAuthorizationRecord:
        """
        Creates a deterministic human authorization record.
        
        Args:
            archive_hash: Hash of the Release Governance Archive being reviewed.
            authorizer_id: Stable identifier of the human reviewer.
            review_intent: Intent (REVIEW_INTENT_APPROVE, REVIEW_INTENT_REJECT, REVIEW_INTENT_DEFER).
            rationale: Reason for the decision.
            authorization_epoch: Deterministic epoch counter.
            authorization_seq: Sequence in epoch.
            
        Returns:
            A frozen HumanAuthorizationRecord.
        """
        # The HumanAuthorizationRecord __post_init__ handles validation of inputs.
        return HumanAuthorizationRecord(
            archive_hash=archive_hash,
            authorizer_id=authorizer_id,
            review_intent=review_intent,
            rationale=rationale,
            authorization_epoch=authorization_epoch,
            authorization_seq=authorization_seq,
        )

    @staticmethod
    def create_summary(record: HumanAuthorizationRecord) -> HumanAuthorizationSummary:
        """
        Produces a deterministic summary of the record.
        """
        return HumanAuthorizationSummary(
            archive_hash=record.archive_hash,
            authorizer_id=record.authorizer_id,
            review_intent=record.review_intent,
            authorization_epoch=record.authorization_epoch,
            authorization_seq=record.authorization_seq,
            record_hash=record.record_hash,
        )
