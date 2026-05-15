import pytest
from src.services.governance.promotion_governance.evidence_package_models import GovernanceEvidencePackage
from src.services.governance.promotion_governance.evidence_package_creator import GovernanceEvidencePackageCreator
from src.services.governance.promotion_governance.archive_models import ReleaseGovernanceArchive
from src.services.governance.promotion_governance.human_auth_models import HumanAuthorizationRecord
from src.services.governance.promotion_governance.evidence_linker_models import HumanReviewEvidenceLink
from src.services.governance.promotion_governance.evidence_package_integrity import (
    EvidencePackageIntegrityGate,
    EvidencePackageIntegrityReport,
)
from src.services.governance.promotion_governance.evidence_package_readiness import (
    EvidencePackageReadinessGate,
    EvidencePackageReadinessReport,
)
from src.services.governance.promotion_governance.evidence_review_summary import (
    EvidenceReviewSummaryBuilder,
    EvidenceReviewSummaryBundle,
)

@pytest.fixture
def mock_archive():
    return ReleaseGovernanceArchive(
        release_id="REL-001",
        certification_artifact_hash="cert-hash",
        gatekeeper_report_hash="gate-hash",
        authorization_hash="auth-hash",
        advisory_decision="APPROVE",
        passed=True,
        reason_codes=("PASS_ALL",),
        evidence_chain=(),
    )

@pytest.fixture
def mock_human_record():
    return HumanAuthorizationRecord(
        archive_hash="cert-hash",
        authorizer_id="user-1",
        review_intent="REVIEW_INTENT_APPROVE",
        rationale="Verified",
        authorization_epoch=100,
        authorization_seq=1,
    )

@pytest.fixture
def verified_link():
    return HumanReviewEvidenceLink(
        archive_hash="arch-hash",
        record_archive_hash="arch-hash",
        record_hash="rec-hash",
        link_status="LINK_VERIFIED",
        reason_codes=("LINK_OK",),
    )

def test_build_summary_success(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Act
    summary = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    
    # Assert
    assert summary.package_id == "PKG-001"
    assert summary.package_hash == package.package_hash
    assert summary.integrity_report_hash == integrity_report.report_hash
    assert summary.readiness_report_hash == readiness_report.report_hash
    assert summary.readiness_decision == "READY_FOR_HUMAN_REVIEW"
    assert summary.integrity_passed is True
    assert summary.package_status == "PACKAGE_VERIFIED"
    assert "READY_FOR_REVIEW" in summary.reason_codes
    assert "PACKAGE_VERIFIED" in summary.reason_codes
    assert summary.summary_version == EvidenceReviewSummaryBuilder.SUMMARY_VERSION
    assert summary.summary_hash is not None

def test_build_summary_blocked_readiness(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    # Force integrity to pass but readiness to fail (e.g. by creating a fake readiness report)
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    readiness_report = EvidencePackageReadinessReport(
        package_id="PKG-001",
        decision="BLOCKED_INTEGRITY_FAILED",
        reason_codes=("INTEGRITY_CHECK_FAILED",)
    )
    
    # Act
    summary = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    
    # Assert
    assert summary.readiness_decision == "BLOCKED_INTEGRITY_FAILED"
    assert "INTEGRITY_CHECK_FAILED" in summary.reason_codes
    assert summary.integrity_passed is True #- based on the provided integrity_report

def test_build_summary_failed_integrity(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    # Force integrity failure
    integrity_report = EvidencePackageIntegrityReport(
        passed=False,
        violations=(),
        package_id="PKG-001",
        expected_version=version
    )
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Act
    summary = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    
    # Assert
    assert summary.integrity_passed is False
    assert summary.readiness_decision == "BLOCKED_INTEGRITY_FAILED"
    assert "INTEGRITY_CHECK_FAILED" in summary.reason_codes

def test_summary_determinism(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Act
    summary1 = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    summary2 = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    
    # Assert
    assert summary1.summary_hash == summary2.summary_hash
    assert summary1.to_dict() == summary2.to_dict()

def test_reason_codes_canonicalization(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    # Readiness report with unsorted reasons
    readiness_report = EvidencePackageReadinessReport(
        package_id="PKG-001",
        decision="READY_FOR_HUMAN_REVIEW",
        reason_codes=("Z", "A")
    )
    
    # Act
    summary = EvidenceReviewSummaryBuilder.build_summary(package, integrity_report, readiness_report)
    
    # Assert
    # sorted("Z", "A", "PACKAGE_VERIFIED") -> ("A", "PACKAGE_VERIFIED", "Z")
    assert summary.reason_codes == tuple(sorted(list(package.reason_codes) + list(readiness_report.reason_codes)))
