"""
Deterministic advisory readiness gate for Governance Evidence Packages.

Requirements:
- No filesystem/database I/O
- No mutation
- Deterministic report generation
- Advisory only: does not authorize release, only assesses readiness for review
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Tuple, Literal

from src.services.governance.promotion_governance.evidence_package_models import (
    GovernanceEvidencePackage,
    canonical_json,
)
from src.services.governance.promotion_governance.evidence_package_integrity import (
    EvidencePackageIntegrityReport,
)

ReadinessDecision = Literal[
    "READY_FOR_HUMAN_REVIEW",
    "BLOCKED_INTEGRITY_FAILED",
    "BLOCKED_PACKAGE_INVALID",
    "BLOCKED_INPUT_INCONSISTENT",
]

@dataclass(frozen=True)
class EvidencePackageReadinessReport:
    """
    Deterministic advisory report stating if an evidence package is structurally ready for review.
    """
    package_id: str
    decision: ReadinessDecision
    reason_codes: Tuple[str, ...]

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic report hash."""
        return {
            "decision": self.decision,
            "package_id": self.package_id,
            "reason_codes": self.reason_codes,
        }

    @property
    def report_hash(self) -> str:
        """Deterministic SHA256 hash of the report identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full deterministic dictionary representation including the hash."""
        return {
            **self.identity_payload(),
            "report_hash": self.report_hash,
        }

class EvidencePackageReadinessGate:
    """
    Deterministic readiness evaluator for Governance Evidence Packages.
    """

    @classmethod
    def evaluate_readiness(
        cls, 
        package: GovernanceEvidencePackage, 
        integrity_report: EvidencePackageIntegrityReport
    ) -> EvidencePackageReadinessReport:
        """
        Evaluates whether a package and its corresponding integrity report 
        are structurally ready for human review.
        """
        
        # 1. Input Consistency Check
        # Both must agree on the package_id if provided in both
        if (integrity_report.package_id and package.package_id and 
            integrity_report.package_id != package.package_id):
            return EvidencePackageReadinessReport(
                package_id=package.package_id,
                decision="BLOCKED_INPUT_INCONSISTENT",
                reason_codes=("INPUT_ID_MISMATCH",)
            )

        # 2. Integrity Check
        if not integrity_report.passed:
            return EvidencePackageReadinessReport(
                package_id=package.package_id,
                decision="BLOCKED_INTEGRITY_FAILED",
                reason_codes=("INTEGRITY_CHECK_FAILED",)
            )

        # 3. Package Validity Check
        if package.package_status != "PACKAGE_VERIFIED":
            return EvidencePackageReadinessReport(
                package_id=package.package_id,
                decision="BLOCKED_PACKAGE_INVALID",
                reason_codes=("PACKAGE_STATUS_NOT_VERIFIED",)
            )

        # 4. Ready
        return EvidencePackageReadinessReport(
            package_id=package.package_id,
            decision="READY_FOR_HUMAN_REVIEW",
            reason_codes=("READY_FOR_REVIEW",)
        )
