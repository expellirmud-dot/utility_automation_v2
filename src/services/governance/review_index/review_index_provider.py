"""
Deterministic provider for Governance Review Index projections.

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
from src.services.governance.promotion_governance.evidence_review_summary_provider import (
    EvidenceReviewSummaryProvider,
)
from src.services.governance.review_index.review_index_builder import (
    GovernanceReviewIndexBuilder,
)

class GovernanceReviewIndexResponse(BaseModel):
    index: dict[str, Any]

class GovernanceReviewIndexProvider:
    """
    Provider for deterministic Governance Review Index projection data.
    """

    @classmethod
    def get_index_projection(cls) -> GovernanceReviewIndexResponse:
        """
        Returns a deterministic projection of the Governance Review Index Bundle.
        Orchestrates various providers to gather references and build the index.
        """
        # 1. Gather deterministic projection data from other providers
        package_data = EvidencePackageProvider.get_evidence_package_projection().package
        integrity_data = EvidencePackageIntegrityProvider.get_integrity_projection().report
        readiness_data = EvidencePackageReadinessProvider.get_readiness_projection().report
        summary_data = EvidenceReviewSummaryProvider.get_summary_projection().summary
        
        # 2. Extract hashes for the builder
        # Use safe extraction to avoid fabricating provenance.
        # Currently, source projections may not contain these hashes.
        certification_hash = cls._safe_extract_hash(package_data, "certification_hash")
        promotion_hash = cls._safe_extract_hash(package_data, "promotion_hash")
        
        # 3. Build the deterministic index bundle
        index_bundle = GovernanceReviewIndexBuilder.build(
            certification_hash=certification_hash,
            promotion_hash=promotion_hash,
            evidence_package_hash=package_data.get("package_hash"),
            integrity_report_hash=integrity_data.get("report_hash"),
            readiness_report_hash=readiness_data.get("report_hash"),
            review_summary_hash=summary_data.get("summary_hash"),
            readiness_decision=readiness_data.get("decision"),
            integrity_passed=integrity_data.get("passed", False),
            invariant_keys=(),
            reason_codes=tuple(package_data.get("reason_codes", [])),
        )
        
        return GovernanceReviewIndexResponse(
            index=index_bundle.to_dict()
        )

    @staticmethod
    def _safe_extract_hash(data: Any, key: str) -> Optional[str]:
        """
        Safely extracts a hash from a projection dictionary.
        Returns None if the data is not a dict, the key is missing, the value is empty,
        or the value is not a valid 64-character hex string.
        """
        if isinstance(data, dict):
            val = data.get(key)
            if isinstance(val, str):
                val = val.strip()
                if val and len(val) == 64 and all(c in '0123456789abcdef' for c in val.lower()):
                    return val
        return None
