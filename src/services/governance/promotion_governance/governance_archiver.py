"""
Governance Archiver for producing deterministic release governance archives.

Requirements:
- Consume governance artifacts
- Produce deterministic ReleaseGovernanceArchive
- No runtime execution authority
- No ledger mutation
- No mesh/quorum calls
- No src.tests.* imports
"""

from __future__ import annotations

from typing import Optional, Tuple
from src.services.governance.promotion_governance.archive_models import (
    ReleaseGovernanceArchive,
    ReleaseGovernanceEvidenceRef,
)
from src.services.governance.certification.models import CertificationArtifact
from src.services.governance.promotion_governance.gatekeeper_models import PromotionGatekeeperReport
from src.services.governance.promotion_governance.authorization_models import ReleaseAuthorizationBundle
from src.services.governance.promotion_governance.promotion_models import PromotionBundle


class GovernanceArchiver:
    """
    Deterministic archiver that aggregates evidence from the governance chain.
    """

    @staticmethod
    def archive(
        release_id: str,
        certification: CertificationArtifact,
        gatekeeper: PromotionGatekeeperReport,
        authorization: ReleaseAuthorizationBundle,
        promotion: Optional[PromotionBundle] = None,
    ) -> ReleaseGovernanceArchive:
        """
        Creates a deterministic governance archive.
        
        Args:
            release_id: Explicit identifier for the release.
            certification: Completed certification artifact.
            gatekeeper: Completed gatekeeper report.
            authorization: Completed authorization bundle.
            promotion: Optional promotion bundle if applicable.
            
        Returns:
            A frozen ReleaseGovernanceArchive.
        """
        if not release_id:
            raise ValueError("release_id is required for archive generation")

        # Build evidence chain in stable order
        # 10 certification, 20 gatekeeper, 30 promotion, 40 authorization
        evidence: list[ReleaseGovernanceEvidenceRef] = []

        # 10: Certification
        evidence.append(
            ReleaseGovernanceEvidenceRef(
                stage="certification",
                artifact_type="CertificationArtifact",
                artifact_hash=certification.artifact_hash,
                passed=certification.passed,
            )
        )

        # 20: Gatekeeper
        evidence.append(
            ReleaseGovernanceEvidenceRef(
                stage="gatekeeper",
                artifact_type="PromotionGatekeeperReport",
                artifact_hash=gatekeeper.report_hash,
                advisory_decision=gatekeeper.advisory_decision,
                passed=gatekeeper.passed,
            )
        )

        # 30: Promotion (Optional)
        promotion_hash = None
        if promotion:
            promotion_hash = promotion.bundle_hash
            evidence.append(
                ReleaseGovernanceEvidenceRef(
                    stage="promotion_governance",
                    artifact_type="PromotionBundle",
                    artifact_hash=promotion.bundle_hash,
                    # PromotionDecision is inside the bundle
                    advisory_decision=promotion.decision.decision,
                    passed=promotion.decision.decision == "approved",
                )
            )

        # 40: Authorization
        evidence.append(
            ReleaseGovernanceEvidenceRef(
                stage="release_authorization",
                artifact_type="ReleaseAuthorizationBundle",
                artifact_hash=authorization.authorization_hash,
                advisory_decision=authorization.advisory_decision,
                passed=authorization.passed,
            )
        )

        # reason_codes must be sorted canonically (sorted by authorization bundle)
        reason_codes = tuple(sorted(authorization.reason_codes))

        return ReleaseGovernanceArchive(
            release_id=release_id,
            certification_artifact_hash=certification.artifact_hash,
            gatekeeper_report_hash=gatekeeper.report_hash,
            authorization_hash=authorization.authorization_hash,
            promotion_bundle_hash=promotion_hash,
            advisory_decision=authorization.advisory_decision,
            passed=authorization.passed,
            reason_codes=reason_codes,
            evidence_chain=tuple(evidence),
        )
