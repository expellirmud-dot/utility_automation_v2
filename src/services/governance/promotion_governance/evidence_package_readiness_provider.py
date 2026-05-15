"""
Deterministic provider for Evidence Package Readiness projections.

Requirements:
- No filesystem I/O
- No database I/O
- No mutation
- Deterministic static projection only
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel

from src.services.governance.promotion_governance.evidence_package_readiness import (
    EvidencePackageReadinessGate,
)
from src.services.governance.promotion_governance.evidence_package_provider import (
    EvidencePackageProvider,
)
from src.services.governance.promotion_governance.evidence_package_integrity_provider import (
    EvidencePackageIntegrityProvider,
)

class EvidencePackageReadinessResponse(BaseModel):
    report: dict[str, Any]

class EvidencePackageReadinessProvider:
    """
    Provider for deterministic Evidence Package Readiness projection data.
    """

    @classmethod
    def get_readiness_projection(cls) -> EvidencePackageReadinessResponse:
        """
        Returns a deterministic projection of a readiness report.
        Uses sample data from package and integrity providers.
        """
        # 1. Get deterministic sample package
        package_data = EvidencePackageProvider.get_evidence_package_projection().package
        
        # 2. Get deterministic integrity report (as a dict)
        integrity_data = EvidencePackageIntegrityProvider.get_integrity_projection().report
        
        # We need to convert the raw dicts back to the models for the Gate to work
        # But since we are in a provider producing a projection, we use the models 
        # to evaluate.
        
        from src.services.governance.promotion_governance.evidence_package_models import GovernanceEvidencePackage
        from src.services.governance.promotion_governance.evidence_package_integrity import EvidencePackageIntegrityReport
        from src.services.governance.promotion_governance.evidence_package_integrity import EvidencePackageIntegrityViolation

        # Reconstruct Package
        package = GovernanceEvidencePackage(**package_data)
        
        # Reconstruct Integrity Report
        violations = tuple(
            EvidencePackageIntegrityViolation(**v) for v in integrity_data.get("violations", [])
        )
        integrity_report = EvidencePackageIntegrityReport(
            passed=integrity_data.get("passed", False),
            violations=violations,
            package_id=integrity_data.get("package_id"),
            expected_version=integrity_data.get("expected_version")
        )
        
        # 3. Run the Readiness Gate
        report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
        
        return EvidencePackageReadinessResponse(
            report=report.to_dict()
        )
