"""
Service to build deterministic Governance Review Index Bundle artifacts.

Requirements:
- No filesystem/database I/O
- No mutation
- Deterministic bundle generation
- Advisory only: consolidates governance references
"""

from __future__ import annotations

import hashlib
from typing import Any, Tuple, Optional

from src.services.governance.review_index.review_index_models import (
    GovernanceReviewIndexBundle,
    IndexStatus,
    canonical_json,
)


class GovernanceReviewIndexBuilder:
    """
    Builder for creating deterministic GovernanceReviewIndexBundle artifacts.
    """

    INDEX_VERSION = "task-065-review-index-v1"

    @classmethod
    def build(
        cls,
        certification_hash: Optional[str],
        promotion_hash: Optional[str],
        evidence_package_hash: Optional[str],
        integrity_report_hash: Optional[str],
        readiness_report_hash: Optional[str],
        review_summary_hash: Optional[str],
        readiness_decision: Optional[str],
        integrity_passed: Optional[bool],
        invariant_keys: Tuple[str, ...],
        reason_codes: Tuple[str, ...],
    ) -> GovernanceReviewIndexBundle:
        """
        Builds a deterministic Governance Review Index Bundle.
        
        If critical references are missing, produces INDEX_BLOCKED_MISSING_REFERENCE.
        """
        
        # 1. Canonicalize reason codes and invariant keys
        sorted_reasons = tuple(sorted(list(reason_codes)))
        sorted_invariants = tuple(sorted(list(invariant_keys)))

        # 2. Determine Status and resolve missing references
        status: IndexStatus = "INDEX_READY"
        
        # Check for missing critical references
        critical_refs = {
            "certification_artifact_hash": certification_hash,
            "promotion_governance_hash": promotion_hash,
            "evidence_package_hash": evidence_package_hash,
            "integrity_report_hash": integrity_report_hash,
            "readiness_report_hash": readiness_report_hash,
            "review_summary_hash": review_summary_hash,
        }
        
        missing_refs = [k for k, v in critical_refs.items() if not v]
        
        if missing_refs:
            status = "INDEX_BLOCKED_MISSING_REFERENCE"
            # Add missing ref info to reason codes if not already present
            reasons = set(sorted_reasons)
            for ref in missing_refs:
                reasons.add(f"MISSING_{ref.upper()}")
            sorted_reasons = tuple(sorted(list(reasons)))
        elif not integrity_passed:
            status = "INDEX_BLOCKED_INTEGRITY_FAILED"
        elif readiness_decision != "READY_FOR_HUMAN_REVIEW":
            status = "INDEX_BLOCKED_READINESS_FAILED"

        # 3. Calculate identity payload and hash
        # We use empty strings for missing refs in the payload to maintain determinism
        identity_payload = {
            "certification_artifact_hash": certification_hash or "",
            "evidence_package_hash": evidence_package_hash or "",
            "index_status": status,
            "index_version": cls.INDEX_VERSION,
            "integrity_passed": integrity_passed if integrity_passed is not None else False,
            "integrity_report_hash": integrity_report_hash or "",
            "invariant_keys": sorted_invariants,
            "promotion_governance_hash": promotion_hash or "",
            "readiness_decision": readiness_decision or "UNKNOWN",
            "readiness_report_hash": readiness_report_hash or "",
            "reason_codes": sorted_reasons,
            "review_summary_hash": review_summary_hash or "",
        }
        
        index_hash = hashlib.sha256(
            canonical_json(identity_payload).encode("utf-8")
        ).hexdigest()

        return GovernanceReviewIndexBundle(
            index_version=cls.INDEX_VERSION,
            index_status=status,
            certification_artifact_hash=certification_hash or "",
            promotion_governance_hash=promotion_hash or "",
            evidence_package_hash=evidence_package_hash or "",
            integrity_report_hash=integrity_report_hash or "",
            readiness_report_hash=readiness_report_hash or "",
            review_summary_hash=review_summary_hash or "",
            readiness_decision=readiness_decision or "UNKNOWN",
            integrity_passed=integrity_passed if integrity_passed is not None else False,
            invariant_keys=sorted_invariants,
            reason_codes=sorted_reasons,
            index_hash=index_hash,
        )
