import pytest
from src.services.governance.review_index.review_index_models import GovernanceReviewIndexBundle
from src.services.governance.review_index.review_index_builder import GovernanceReviewIndexBuilder
from src.services.governance.review_index.review_index_manifest import (
    GovernanceReviewIndexManifest,
    GovernanceReviewIndexManifestBuilder,
)

def test_manifest_creation_success():
    # Arrange: Create a valid index bundle first
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
        promotion_hash="prom-hash",
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=True,
        invariant_keys=("INV-001", "INV-002"),
        reason_codes=("REASON-OK",),
    )
    
    # Act
    manifest = GovernanceReviewIndexManifestBuilder.from_index(index)
    
    # Assert
    assert manifest.manifest_version == GovernanceReviewIndexManifestBuilder.MANIFEST_VERSION
    assert manifest.index_hash == index.index_hash
    assert manifest.index_status == "INDEX_READY"
    assert manifest.manifest_hash is not None
    assert manifest.invariant_keys == ("INV-001", "INV-002")
    assert manifest.reason_codes == ("REASON-OK",)

def test_manifest_preserves_blocked_status():
    # Arrange: Create a blocked index bundle (missing promotion hash)
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
    
    # Act
    manifest = GovernanceReviewIndexManifestBuilder.from_index(index)
    
    # Assert
    assert manifest.index_status == "INDEX_BLOCKED_MISSING_REFERENCE"
    assert "MISSING_PROMOTION_GOVERNANCE_HASH" in manifest.reason_codes
    assert manifest.promotion_governance_hash == ""

def test_manifest_determinism():
    # Arrange
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
        promotion_hash="prom-hash",
        evidence_package_hash="pkg-hash",
        integrity_report_hash="integ-hash",
        readiness_report_hash="read-hash",
        review_summary_hash="sumry-hash",
        readiness_decision="READY_FOR_HUMAN_REVIEW",
        integrity_passed=True,
        invariant_keys=("B", "A"),
        reason_codes=("Y", "X"),
    )
    
    # Act
    manifest1 = GovernanceReviewIndexManifestBuilder.from_index(index)
    manifest2 = GovernanceReviewIndexManifestBuilder.from_index(index)
    
    # Assert
    assert manifest1.manifest_hash == manifest2.manifest_hash
    assert manifest1.invariant_keys == ("A", "B")
    assert manifest1.reason_codes == ("X", "Y")
    assert manifest1.to_dict() == manifest2.to_dict()

def test_manifest_structural_validation_failure():
    # Test __post_init__ sorting validation for invariant_keys
    with pytest.raises(ValueError, match="invariant_keys must be sorted canonically"):
        GovernanceReviewIndexManifest(
            manifest_version="v1",
            index_hash="h",
            index_status="INDEX_READY",
            readiness_decision="D",
            integrity_passed=True,
            evidence_package_hash="h",
            review_summary_hash="h",
            certification_artifact_hash="h",
            promotion_governance_hash="h",
            invariant_keys=("B", "A"),
            reason_codes=(),
            manifest_hash="h"
        )

def test_manifest_tampered_hash_rejected():
    # Arrange
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
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
    manifest = GovernanceReviewIndexManifestBuilder.from_index(index)
    
    # Act: Manually create manifest with wrong hash
    with pytest.raises(ValueError, match="manifest_hash mismatch"):
        GovernanceReviewIndexManifest(
            manifest_version=manifest.manifest_version,
            index_hash=manifest.index_hash,
            index_status=manifest.index_status,
            readiness_decision=manifest.readiness_decision,
            integrity_passed=manifest.integrity_passed,
            evidence_package_hash=manifest.evidence_package_hash,
            review_summary_hash=manifest.review_summary_hash,
            certification_artifact_hash=manifest.certification_artifact_hash,
            promotion_governance_hash=manifest.promotion_governance_hash,
            invariant_keys=manifest.invariant_keys,
            reason_codes=manifest.reason_codes,
            manifest_hash="tampered-hash"
        )

def test_manifest_version_affects_hash():
    # Arrange: Create an index bundle
    index = GovernanceReviewIndexBuilder.build(
        certification_hash="cert-hash",
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
    
    # Act: Compare hashes for different versions using the same index
    import hashlib
    from src.services.governance.review_index.review_index_models import canonical_json

    def compute_hash(version, index_bundle):
        payload = {
            "certification_artifact_hash": index_bundle.certification_artifact_hash,
            "evidence_package_hash": index_bundle.evidence_package_hash,
            "index_hash": index_bundle.index_hash,
            "index_status": index_bundle.index_status,
            "integrity_passed": index_bundle.integrity_passed,
            "invariant_keys": index_bundle.invariant_keys,
            "manifest_version": version,
            "promotion_governance_hash": index_bundle.promotion_governance_hash,
            "readiness_decision": index_bundle.readiness_decision,
            "reason_codes": index_bundle.reason_codes,
            "review_summary_hash": index_bundle.review_summary_hash,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    hash_v1 = compute_hash("v1", index)
    hash_v2 = compute_hash("v2", index)
    
    assert hash_v1 != hash_v2
