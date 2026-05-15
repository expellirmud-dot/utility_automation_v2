"""
Deterministic provider for Governance Evidence Package projections.

Requirements:
- No filesystem I/O
- No database I/O
- No mutation
- Deterministic static projection only
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel

from src.services.governance.promotion_governance.evidence_package_models import (
    GovernanceEvidencePackage,
)

class EvidencePackageResponse(BaseModel):
    package: dict[str, Any]

class EvidencePackageProvider:
    """
    Provider for deterministic Governance Evidence Package projection data.
    """
    
    # Static deterministic sample data
    _SAMPLE_PACKAGE = GovernanceEvidencePackage(
        package_id="pkg-det-001",
        package_version="task-056-evidence-package-v1",
        archive_hash="a" * 64,
        human_record_hash="b" * 64,
        evidence_link_hash="c" * 64,
        package_status="PACKAGE_VERIFIED",
        reason_codes=("PACKAGE_VERIFIED",),
    )

    @classmethod
    def get_evidence_package_projection(cls) -> EvidencePackageResponse:
        """
        Returns a deterministic projection of the latest evidence package.
        Currently uses static sample data.
        """
        return EvidencePackageResponse(
            package=cls._SAMPLE_PACKAGE.to_dict()
        )
