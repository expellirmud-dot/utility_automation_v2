"""
Deterministic summary bundle for the Governance Evidence Review chain.

Requirements:
- No filesystem/database I/O
- No mutation
- Deterministic report generation
- Advisory only: provides a compact audit summary without granting authority
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Tuple

from src.services.governance.promotion_governance.evidence_package_models import (
    GovernanceEvidencePackage,
    canonical_json,
)
from src.services.governance.promotion_governance.evidence_package_integrity import (
    EvidencePackageIntegrityReport,
)
from src.services.governance.promotion_governance.evidence_package_readiness import (
    EvidencePackageReadinessReport,
)

@dataclass(frozen=True)
class EvidenceReviewSummaryBundle:
    """
    A compact, deterministic summary of the evidence review process.
    """
    package_id: str
    package_hash: str
    integrity_report_hash: str
    readiness_report_hash: str
    readiness_decision: str
    integrity_passed: bool
    package_status: str
    reason_codes: Tuple[str, ...]
    summary_version: str
    summary_hash: str

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic summary hash (excludes summary_hash itself)."""
        return {
            "integrity_passed": self.integrity_passed,
            "integrity_report_hash": self.integrity_report_hash,
            "package_hash": self.package_hash,
            "package_id": self.package_id,
            "package_status": self.package_status,
            "readiness_decision": self.readiness_decision,
            "readiness_report_hash": self.readiness_report_hash,
            "reason_codes": self.reason_codes,
            "summary_version": self.summary_version,
        }

    @property
    def bundle_hash(self) -> str:
        """Deterministic SHA256 hash of the bundle identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "summary_hash": self.bundle_hash,
        }

class EvidenceReviewSummaryBuilder:
    """
    Service to build deterministic EvidenceReviewSummaryBundle artifacts.
    """
    
    SUMMARY_VERSION = "task-062-summary-v1"

    @classmethod
    def build_summary(
        cls,
        package: GovernanceEvidencePackage,
        integrity_report: EvidencePackageIntegrityReport,
        readiness_report: EvidencePackageReadinessReport,
    ) -> EvidenceReviewSummaryBundle:
        """
        Combines evidence package, integrity report, and readiness report 
        into a single deterministic summary bundle.
        """
        
        # Combine and canonicalize reason codes
        all_reasons = set()
        if package.reason_codes:
            all_reasons.update(package.reason_codes)
        if readiness_report.reason_codes:
            all_reasons.update(readiness_report.reason_codes)
        
        sorted_reasons = tuple(sorted(list(all_reasons)))
        
        # Calculate identity payload and hash before constructing the bundle
        # Since EvidenceReviewSummaryBundle is frozen and summary_hash is a field,
        # we compute it here to pass it into the constructor.
        
        identity_payload = {
            "integrity_passed": integrity_report.passed,
            "integrity_report_hash": integrity_report.report_hash,
            "package_hash": package.package_hash,
            "package_id": package.package_id,
            "package_status": package.package_status,
            "readiness_decision": readiness_report.decision,
            "readiness_report_hash": readiness_report.report_hash,
            "reason_codes": sorted_reasons,
            "summary_version": cls.SUMMARY_VERSION,
        }
        
        summary_hash = hashlib.sha256(
            canonical_json(identity_payload).encode("utf-8")
        ).hexdigest()
        
        return EvidenceReviewSummaryBundle(
            package_id=package.package_id,
            package_hash=package.package_hash,
            integrity_report_hash=integrity_report.report_hash,
            readiness_report_hash=readiness_report.report_hash,
            readiness_decision=readiness_report.decision,
            integrity_passed=integrity_report.passed,
            package_status=package.package_status,
            reason_codes=sorted_reasons,
            summary_version=cls.SUMMARY_VERSION,
            summary_hash=summary_hash,
        )
