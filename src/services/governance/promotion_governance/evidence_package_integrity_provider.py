"""
Deterministic provider for Evidence Package Integrity projections.

Requirements:
- No filesystem I/O
- No database I/O
- No mutation
- Deterministic static projection only
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel

from src.services.governance.promotion_governance.evidence_package_integrity import (
    EvidencePackageIntegrityGate,
    EvidencePackageIntegrityReport,
)
from src.services.governance.promotion_governance.evidence_package_provider import (
    EvidencePackageProvider,
)

class EvidencePackageIntegrityResponse(BaseModel):
    report: dict[str, Any]

class EvidencePackageIntegrityProvider:
    """
    Provider for deterministic Evidence Package Integrity projection data.
    """

    @classmethod
    def get_integrity_projection(cls) -> EvidencePackageIntegrityResponse:
        """
        Returns a deterministic projection of an integrity report.
        Currently uses static sample data and the IntegrityGate.
        """
        # Get a deterministic sample package from the existing provider
        package_data = EvidencePackageProvider.get_evidence_package_projection().package
        
        # Run the gate on the sample package
        # We assume the sample package matches the expected version for this projection
        expected_version = "task-056-evidence-package-v1"
        
        # Since the provider provides a dict, we use validate_payload
        report = EvidencePackageIntegrityGate.validate_payload(
            payload=package_data,
            expected_version=expected_version
        )
        
        return EvidencePackageIntegrityResponse(
            report=report.to_dict()
        )
