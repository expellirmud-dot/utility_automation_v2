"""
Deterministic Release Authorization Logic.

Consumes certification artifacts and gatekeeper reports to produce
an advisory authorization bundle. Adheres to fail-closed principles.

No execution authority. Governance visibility only.
"""

from __future__ import annotations

from typing import Tuple
from src.services.governance.certification.models import CertificationArtifact
from src.services.governance.promotion_governance.gatekeeper_models import PromotionGatekeeperReport
from src.services.governance.promotion_governance.authorization_models import (
    ReleaseAuthorizationBundle,
    ReleaseAuthorizationDecision,
)

class ReleaseAuthorizer:
    """
    Evaluates release authorization eligibility based on a frozen 
    certification chain (Artifact -> Gatekeeper Report).
    """

    @staticmethod
    def authorize(
        certification_artifact: CertificationArtifact,
        gatekeeper_report: PromotionGatekeeperReport,
    ) -> ReleaseAuthorizationBundle:
        """
        Determine if a release is eligible for authorization review.
        
        Args:
            certification_artifact: The source certification evidence.
            gatekeeper_report: The advisory report from the Promotion Gatekeeper.
            
        Returns:
            A frozen, hashable ReleaseAuthorizationBundle.
        """
        reason_codes: list[str] = []
        passed = False
        decision: ReleaseAuthorizationDecision = "BLOCKED_INPUT_INCONSISTENT"

        # 1. Validate Input Consistency
        # The gatekeeper report must refer to the same certification artifact provided
        if gatekeeper_report.source_certification_hash != certification_artifact.artifact_hash:
            decision = "BLOCKED_INPUT_INCONSISTENT"
            reason_codes.append("INPUT_HASH_MISMATCH")
            passed = False
        
        # 2. Check Certification Status
        elif not certification_artifact.passed:
            decision = "BLOCKED_CERTIFICATION_FAILED"
            reason_codes.append("CERTIFICATION_FAILED")
            passed = False
            
        # 3. Check Gatekeeper Status
        elif not gatekeeper_report.passed or \
             gatekeeper_report.advisory_decision != "ELIGIBLE_FOR_PROMOTION_REVIEW":
            decision = "BLOCKED_GATEKEEPER_FAILED"
            if not gatekeeper_report.passed:
                reason_codes.append("GATEKEEPER_FAILED")
            if gatekeeper_report.advisory_decision != "ELIGIBLE_FOR_PROMOTION_REVIEW":
                reason_codes.append("GATEKEEPER_NOT_ELIGIBLE")
            passed = False
            
        # 4. Final Eligibility
        else:
            decision = "ELIGIBLE_FOR_RELEASE_AUTHORIZATION_REVIEW"
            reason_codes.append("ALL_GOVERNANCE_CRITERIA_SATISFIED")
            passed = True

        return ReleaseAuthorizationBundle(
            passed=passed,
            advisory_decision=decision,
            source_certification_hash=certification_artifact.artifact_hash,
            source_gatekeeper_hash=gatekeeper_report.report_hash,
            reason_codes=tuple(sorted(reason_codes)),
        )
