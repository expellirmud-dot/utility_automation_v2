"""
Deterministic linker for Human Review Intent evidence.

Requirements:
- Link HumanAuthorizationRecord to ReleaseGovernanceArchive
- Validate hash consistency between record and archive
- No runtime execution authority
- No ledger mutation
- No mesh/quorum calls
- No src.tests.* imports
"""

from __future__ import annotations

from src.services.governance.promotion_governance.evidence_linker_models import HumanReviewEvidenceLink
from src.services.governance.promotion_governance.archive_models import ReleaseGovernanceArchive
from src.services.governance.promotion_governance.human_auth_models import HumanAuthorizationRecord


class HumanReviewEvidenceLinker:
    """
    Deterministic linker that verifies and binds a human review record to a governance archive.
    """

    @staticmethod
    def create_link(
        record: HumanAuthorizationRecord,
        archive: ReleaseGovernanceArchive,
    ) -> HumanReviewEvidenceLink:
        """
        Creates a deterministic evidence link.
        
        Args:
            record: The human authorization record.
            archive: The release governance archive.
            
        Returns:
            A frozen HumanReviewEvidenceLink.
        """
        # Extract hashes for the link
        archive_hash = archive.archive_hash
        record_archive_hash = record.archive_hash
        record_hash = record.record_hash

        # Validate hash consistency
        if record_archive_hash == archive_hash:
            link_status = "LINK_VERIFIED"
            reason_codes = ("LINK_VERIFIED",)
        else:
            # Fail closed on mismatch
            link_status = "LINK_BLOCKED_ARCHIVE_MISMATCH"
            reason_codes = tuple(sorted(("ARCHIVE_HASH_MISMATCH", "LINK_BLOCKED")))

        return HumanReviewEvidenceLink(
            archive_hash=archive_hash,
            record_archive_hash=record_archive_hash,
            record_hash=record_hash,
            link_status=link_status,
            reason_codes=reason_codes,
        )
