"""
Deterministic integrity gate for Governance Evidence Packages.

Requirements:
- No filesystem/database I/O
- No mutation
- Deterministic report generation
- Support for both object and raw payload validation
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Tuple, Optional

from src.services.governance.promotion_governance.evidence_package_models import (
    GovernanceEvidencePackage,
    PackageStatus,
    canonical_json,
)

@dataclass(frozen=True)
class EvidencePackageIntegrityViolation:
    """Deterministic representation of an integrity violation."""
    field: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "reason": self.reason,
        }

@dataclass(frozen=True)
class EvidencePackageIntegrityReport:
    """
    Deterministic report of an evidence package integrity check.
    """
    passed: bool
    violations: Tuple[EvidencePackageIntegrityViolation, ...]
    package_id: Optional[str] = None
    expected_version: Optional[str] = None

    def identity_payload(self) -> dict[str, Any]:
        """Payload for deterministic report hash."""
        return {
            "passed": self.passed,
            "package_id": self.package_id,
            "expected_version": self.expected_version,
            "violations": [v.to_dict() for v in self.violations],
        }

    @property
    def report_hash(self) -> str:
        """Deterministic SHA256 hash of the report identity payload."""
        return hashlib.sha256(
            canonical_json(self.identity_payload()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity_payload(),
            "report_hash": self.report_hash,
        }

class EvidencePackageIntegrityGate:
    """
    Deterministic validator for GovernanceEvidencePackage artifacts.
    """

    @classmethod
    def validate_package(
        cls, 
        package: GovernanceEvidencePackage, 
        expected_version: str
    ) -> EvidencePackageIntegrityReport:
        """
        Validates an existing GovernanceEvidencePackage object.
        """
        violations: list[EvidencePackageIntegrityViolation] = []

        # 1. Version Check
        if package.package_version != expected_version:
            violations.append(EvidencePackageIntegrityViolation(
                field="package_version",
                reason=f"Expected {expected_version}, found {package.package_version}"
            ))

        # 2. Status Check
        # Note: GovernanceEvidencePackage.__post_init__ already checks valid status,
        # but the gate provides a reportable check.
        valid_statuses = {"PACKAGE_VERIFIED", "PACKAGE_INVALID"}
        if package.package_status not in valid_statuses:
            violations.append(EvidencePackageIntegrityViolation(
                field="package_status",
                reason=f"Invalid status: {package.package_status}"
            ))

        # 3. Canonicality Check
        if tuple(sorted(package.reason_codes)) != package.reason_codes:
            violations.append(EvidencePackageIntegrityViolation(
                field="reason_codes",
                reason="Reason codes are not sorted canonically"
            ))

        return EvidencePackageIntegrityReport(
            passed=len(violations) == 0,
            violations=tuple(violations),
            package_id=package.package_id,
            expected_version=expected_version
        )

    @classmethod
    def validate_payload(
        cls, 
        payload: dict[str, Any], 
        expected_version: str
    ) -> EvidencePackageIntegrityReport:
        """
        Validates a raw dictionary payload. 
        Allows detection of hash mismatches and missing fields.
        """
        violations: list[EvidencePackageIntegrityViolation] = []
        package_id = payload.get("package_id")

        # 1. Required Fields Check
        required_fields = {
            "package_id", "package_version", "archive_hash", 
            "human_record_hash", "evidence_link_hash", "package_status", "reason_codes"
        }
        missing = required_fields - set(payload.keys())
        if missing:
            for field in sorted(list(missing)):
                violations.append(EvidencePackageIntegrityViolation(
                    field=field,
                    reason="Required field is missing from payload"
                ))

        if not violations:
            # 2. Hash Verification (The critical check for raw payloads)
            # Recompute the expected hash from identity payload
            identity_payload = {
                "archive_hash": payload.get("archive_hash"),
                "certification_hash": payload.get("certification_hash"),
                "evidence_link_hash": payload.get("evidence_link_hash"),
                "gatekeeper_report_hash": payload.get("gatekeeper_report_hash"),
                "human_record_hash": payload.get("human_record_hash"),
                "package_id": payload.get("package_id"),
                "package_status": payload.get("package_status"),
                "package_version": payload.get("package_version"),
                "promotion_hash": payload.get("promotion_hash"),
                "reason_codes": payload.get("reason_codes"),
            }
            
            expected_hash = hashlib.sha256(
                canonical_json(identity_payload).encode("utf-8")
            ).hexdigest()
            
            actual_hash = payload.get("package_hash")
            if actual_hash != expected_hash:
                violations.append(EvidencePackageIntegrityViolation(
                    field="package_hash",
                    reason=f"Hash mismatch. Expected {expected_hash}, found {actual_hash}"
                ))

            # 3. Version Check
            if payload.get("package_version") != expected_version:
                violations.append(EvidencePackageIntegrityViolation(
                    field="package_version",
                    reason=f"Expected {expected_version}, found {payload.get('package_version')}"
                ))

            # 4. Status Check
            valid_statuses = {"PACKAGE_VERIFIED", "PACKAGE_INVALID"}
            if payload.get("package_status") not in valid_statuses:
                violations.append(EvidencePackageIntegrityViolation(
                    field="package_status",
                    reason=f"Invalid status: {payload.get('package_status')}"
                ))

            # 5. Canonicality Check
            reasons = payload.get("reason_codes")
            if isinstance(reasons, (list, tuple)):
                if tuple(sorted(reasons)) != tuple(reasons):
                    violations.append(EvidencePackageIntegrityViolation(
                        field="reason_codes",
                        reason="Reason codes are not sorted canonically"
                    ))
            else:
                violations.append(EvidencePackageIntegrityViolation(
                    field="reason_codes",
                    reason="reason_codes must be a list or tuple"
                ))

        return EvidencePackageIntegrityReport(
            passed=len(violations) == 0,
            violations=tuple(violations),
            package_id=package_id,
            expected_version=expected_version
        )
