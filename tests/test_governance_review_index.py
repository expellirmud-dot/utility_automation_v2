import pytest
from src.services.governance.review_index.review_index_builder import GovernanceReviewIndexBuilder
from src.services.governance.review_index.review_index_models import GovernanceReviewIndexBundle

def test_build_index_success():
    # Arrange
    certs = "cert-hash"
    prom = "prom-hash"
    pkg = "pkg-hash"
    integ = "integ-hash"
    read = "read-hash"
    sumry = "sumry-hash"
    
    # Act
    index = GovernanceReviewIndexBuilder.build(
        certification_hash=certs,
        promotion_hash=prom,
        evidence_package_hash=pkg,
        integrity_report_hash=integ,
        readiness_report_hash=read,
        review_summary_hash=sumry,
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=True,
        invariant_keys=("INV-001", "INV-002"),
        reason_codes=("REASON-OK",),
    )
    
    # Assert
    assert index.index_status == "INDEX_READY"
    assert index.certification_artifact_hash == certs
    assert index.index_hash is not None
    assert index.index_version == GovernanceReviewIndexBuilder.INDEX_VERSION
    assert index.invariant_keys == ("INV-001", "INV-002")

def test_build_index_missing_reference():
    # Arrange
    # missing promotion_hash
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
        promotion_hash=None,
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=True,
        invariant_keys=(),
        reason_codes=(),
    )
    
    # Assert
    assert index.index_status == "INDEX_BLOCKED_MISSING_REFERENCE"
    assert "MISSING_PROMOTION_GOVERNANCE_HASH" in index.reason_codes
    assert index.promotion_governance_hash == ""

def test_build_index_empty_string_reference():
    # Arrange
    # empty string for certification_hash
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="",
        promotion_hash="prom-hash",
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=True,
        invariant_keys=(),
        reason_codes=(),
    )
    
    # Assert
    assert index.index_status == "INDEX_BLOCKED_MISSING_REFERENCE"
    assert "MISSING_CERTIFICATION_ARTIFACT_HASH" in index.reason_codes

def test_build_index_integrity_failed():
    # Arrange
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
        promotion_hash="prom-hash",
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=False,
        invariant_keys=(),
        reason_codes=(),
    )
    
    # Assert
    assert index.index_status == "INDEX_BLOCKED_INTEGRITY_FAILED"

def test_build_index_readiness_failed():
    # Arrange
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
        promotion_hash="prom-hash",
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="BLOCKED_INPUT_INCONSISTENT",
        integrity_passed=True,
        invariant_keys=(),
        reason_codes=(),
    )
    
    # Assert
    assert index.index_status == "INDEX_BLOCKED_READINESS_FAILED"

def test_index_determinism():
    # Arrange
    params = {
        "certification_hash": "cert-hash",
        "promotion_hash": "prom-hash",
        "evidence_package_hash": "pkg-hash",
        "integrity_report_hash": "integ-hash",
        "readiness_report_hash": "read-hash",
        "review_summary_hash": "sumry-hash",
        "readiness_decision": "READY_FOR_HUMAN_REVIEW",
        "integrity_passed": True,
        "invariant_keys": ("B", "A"),
        "reason_codes": ("Y", "X"),
    }
    
    # Act
    index1 = GovernanceReviewIndexBuilder.build(**params)
    index2 = GovernanceReviewIndexBuilder.build(**params)
    
    # Assert
    assert index1.index_hash == index2.index_hash
    assert index1.invariant_keys == ("A", "B")
    assert index1.reason_codes == ("X", "Y")
    assert index1.to_dict() == index2.to_dict()

def test_reason_merge_determinism():
    # Arrange
    params1 = {
        "certification_hash": "cert-hash",
        "promotion_hash": "prom-hash",
        "evidence_package_hash": "pkg-hash",
        "integrity_report_hash": "integ-hash",
        "readiness_report_hash": "read-hash",
        "review_summary_hash": "sumry-hash",
        "readiness_decision": "READY_FOR_HUMAN_REVIEW",
        "integrity_passed": True,
        "invariant_keys": (),
        "reason_codes": ("R1", "R2"),
    }
    params2 = params1.copy()
    params2["reason_codes"] = ("R2", "R1")
    
    # Act
    index1 = GovernanceReviewIndexBuilder.build(**params1)
    index2 = GovernanceReviewIndexBuilder.build(**params2)
    
    # Assert
    assert index1.reason_codes == index2.reason_codes
    assert index1.index_hash == index2.index_hash

def test_structural_validation_failure():
    # Test __post_init__ validation
    with pytest.raises(ValueError, match="index_version is required"):
        GovernanceReviewIndexBundle(
            index_version="",
            index_status="INDEX_READY",
            certification_artifact_hash="h",
            promotion_governance_hash="h",
            evidence_package_hash="h",
            integrity_report_hash="h",
            readiness_report_hash="h",
            review_summary_hash="h",
            readiness_decision="D",
            integrity_passed=True,
            invariant_keys=(),
            reason_codes=(),
            index_hash="h"
        )

def test_invalid_status_rejected():
    # Test __post_init__ status validation
    with pytest.raises(ValueError, match="Invalid index_status"):
        GovernanceReviewIndexBundle(
            index_version="v1",
            index_status="INVALID_STATUS",
            certification_artifact_hash="h",
            promotion_governance_hash="h",
            evidence_package_hash="h",
            integrity_report_hash="h",
            readiness_report_hash="h",
            review_summary_hash="h",
            readiness_decision="D",
            integrity_passed=True,
            invariant_keys=(),
            reason_codes=(),
            index_hash="h"
        )

def test_tampered_hash_rejected():
    # Test __post_init__ hash validation
    with pytest.raises(ValueError, match="index_hash mismatch"):
        GovernanceReviewIndexBundle(
            index_version="v1",
            index_status="INDEX_READY",
            certification_artifact_hash="h",
            promotion_governance_hash="h",
            evidence_package_hash="h",
            integrity_report_hash="h",
            readiness_report_hash="h",
            review_summary_hash="h",
            readiness_decision="D",
            integrity_passed=True,
            invariant_keys=(),
            reason_codes=(),
            index_hash="tampered-hash"
        )

def test_invalid_canonical_ordering_rejected():
    # Test __post_init__ ordering validation
    with pytest.raises(ValueError, match="invariant_keys must be sorted canonically"):
        GovernanceReviewIndexBundle(
            index_version="v1",
            index_status="INDEX_READY",
            certification_artifact_hash="h",
            promotion_governance_hash="h",
            evidence_package_hash="h",
            integrity_report_hash="h",
            readiness_report_hash="h",
            review_summary_hash="h",
            readiness_decision="D",
            integrity_passed=True,
            invariant_keys=("B", "A"),
            reason_codes=(),
            index_hash="h" # This will actually fail on hash first if we don't calculate it
        )
    
    # To properly test ordering rejection, we need a valid hash for the unsorted input 
    # (which is impossible by definition of the class's logic) or just accept that
    # the ordering check comes before the hash check in __post_init__.
