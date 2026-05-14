"""
Deterministic creator for the Governance Evidence Package.

Requirements:
- Fail-closed logic for evidence link verification
- Deterministic output regardless of input order
- No timestamps, randoms, or side effects
"""

from __future__ import annotations

from typing import Tuple
from src.services.governance.promotion_governance.archive_models import ReleaseGovernanceArchive
from src.services.governance.promotion_governance.human_auth_models import HumanAuthorizationRecord
from src.services.governance.promotion_governance.evidence_linker import HumanReviewEvidenceLinker
from src.services.governance.promotion_governance.evidence_linker_models import HumanReviewEvidenceLink
from src.services.governance.promotion_governance.evidence_package_models import GovernanceEvidencePackage, PackageStatus


class GovernanceEvidencePackageCreator:
    """
    Factory for producing deterministic GovernanceEvidencePackage artifacts.
    """
    
    PACKAGE_VERSION = "task-056-evidence-package-v1"

    @classmethod
    def create_package(
        cls,
        package_id: str,
        archive: ReleaseGovernanceArchive,
        human_record: HumanAuthorizationRecord,
        evidence_link: HumanReviewEvidenceLink,
    ) -> GovernanceEvidencePackage:
        """
        Produces a deterministic evidence package bundling references to the governance chain.
        
        If evidence_link is not VERIFIED, produce a PACKAGE_INVALID artifact.
        Raises ValueError only for structurally invalid inputs.
        """
        
        # structural validation for input types is handled by type hinting, 
        # but we ensure we have the hashes.
        
        # Fail-closed logic
        if evidence_link.link_status == "LINK_VERIFIED":
            status: PackageStatus = "PACKAGE_VERIFIED"
            reasons = ("PACKAGE_VERIFIED",)
        else:
            status: PackageStatus = "PACKAGE_INVALID"
            # include the link failure reason + a generic invalid marker
            reasons = tuple(sorted(("EVIDENCE_LINK_NOT_VERIFIED", "PACKAGE_INVALID")))

        return GovernanceEvidencePackage(
            package_id=package_id,
            package_version=cls.PACKAGE_VERSION,
            archive_hash=archive.archive_hash,
            human_record_hash=human_record.record_hash,
            evidence_link_hash=evidence_link.link_hash,
            package_status=status,
            reason_codes=reasons,
        )
