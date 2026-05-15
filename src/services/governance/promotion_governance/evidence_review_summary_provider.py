"""
Deterministic provider for Evidence Review Summary projections.

Requirements:
- No filesystem I/O
- No database I/O
- No mutation
- Deterministic static projection only
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel

from src.services.governance.promotion_governance.evidence_package_provider import (
    EvidencePackageProvider,
)
from src.services.governance.promotion_governance.evidence_package_integrity_provider import (
    EvidencePackageIntegrityProvider,
)
from src.services.governance.promotion_governance.evidence_package_readiness_provider import (
    EvidencePackageReadinessProvider,
)
from src.services.governance.promotion_governance.evidence_review_summary import (
    EvidenceReviewSummaryBuilder,
)

class EvidenceReviewSummaryResponse(BaseModel):
    summary: dict[str, Any]

class EvidenceReviewSummaryProvider:
    """
    Provider for deterministic Evidence Review Summary projection data.
    """

    @classmethod
    def get_summary_projection(cls) -> EvidenceReviewSummaryResponse:
        """
        Returns a deterministic projection of an evidence review summary bundle.
        Orchestrates package, integrity, and readiness providers to build the summary.
        """
        # 1. Get deterministic sample package
        package_data = EvidencePackageProvider.get_evidence_package_projection().package
        
        # 2. Get deterministic integrity report
        integrity_data = EvidencePackageIntegrityProvider.get_integrity_projection().report
        
        # 3. Get deterministic readiness report
        readiness_data = EvidencePackageReadinessProvider.get_readiness_projection().report
        
        # Reconstruct models for the Builder
        from src.services.governance.promotion_governance.evidence_package_models import GovernanceEvidencePackage
        from src.services.governance.promotion_governance.evidence_package_integrity import (
            EvidencePackageIntegrityReport,
            EvidencePackageIntegrityViolation,
        )
        from src.services.governance.promotion_governance.evidence_package_readiness import (
            EvidencePackageReadinessReport,
        )

        # Reconstruct Package - sanitize derived fields first
        package_params = {k: v for k, v in package_data.items() if k != "package_hash"}
        package = GovernanceEvidencePackage(**package_params)
        
        violations = tuple(
            EvidencePackageIntegrityViolation(**v) for v in integrity_data.get("violations", [])
        )
        integrity_report = EvidencePackageIntegrityReport(
            passed=integrity_data.get("passed", False),
            violations=violations,
            package_id=integrity_data.get("package_id"),
            expected_version=integrity_data.get("expected_version")
        )
        
        readiness_report = EvidencePackageReadinessReport(
            package_id=readiness_data.get("package_id"),
            decision=readiness_data.get("decision"),
            reason_codes=tuple(readiness_data.get("reason_codes", [])),
        )
        
        # 4. Build the deterministic summary bundle
        summary_bundle = EvidenceReviewSummaryBuilder.build_summary(
            package=package,
            integrity_report=integrity_report,
            readiness_report=readiness_report,
        )
        
        return EvidenceReviewSummaryResponse(
            summary=summary_bundle.to_dict()
        )
