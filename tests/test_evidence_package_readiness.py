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

@pytest.fixture
def unverified_link():
    return HumanReviewEvidenceLink(
        archive_hash="arch-hash",
        record_archive_hash="wrong-hash",
        record_hash="rec-hash",
        link_status="LINK_BLOCKED_ARCHIVE_MISMATCH",
        reason_codes=("MISMATCH",),
    )

def test_readiness_success(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    
    # Act
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Assert
    assert readiness_report.decision == "READY_FOR_HUMAN_REVIEW"
    assert "READY_FOR_REVIEW" in readiness_report.reason_codes
    assert readiness_report.package_id == "PKG-001"

def test_readiness_blocked_input_inconsistent(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    # Manually create an integrity report with a different package_id
    integrity_report = EvidencePackageIntegrityReport(
        passed=True,
        violations=(),
        package_id="PKG-WRONG",
        expected_version=version
    )
    
    # Act
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Assert
    assert readiness_report.decision == "BLOCKED_INPUT_INCONSISTENT"
    assert "INPUT_ID_MISMATCH" in readiness_report.reason_codes

def test_readiness_blocked_integrity_failed(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    # Force integrity failure
    integrity_report = EvidencePackageIntegrityReport(
        passed=False,
        violations=(), # Simplification for test
        package_id="PKG-001",
        expected_version=version
    )
    
    # Act
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Assert
    assert readiness_report.decision == "BLOCKED_INTEGRITY_FAILED"
    assert "INTEGRITY_CHECK_FAILED" in readiness_report.reason_codes

def test_readiness_blocked_package_invalid(mock_archive, mock_human_record, unverified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    # Create an invalid package
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, unverified_link
    )
    # Package is structurally valid (hash is correct), but status is PACKAGE_INVALID
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    
    # Act
    readiness_report = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Assert
    assert readiness_report.decision == "BLOCKED_PACKAGE_INVALID"
    assert "PACKAGE_STATUS_NOT_VERIFIED" in readiness_report.reason_codes

def test_report_determinism(mock_archive, mock_human_record, verified_link):
    # Arrange
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    integrity_report = EvidencePackageIntegrityGate.validate_package(package, version)
    
    # Act
    report1 = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    report2 = EvidencePackageReadinessGate.evaluate_readiness(package, integrity_report)
    
    # Assert
    assert report1.report_hash == report2.report_hash
    assert report1.to_dict() == report2.to_dict()

def test_readiness_projection_reconstruction_with_hash():
    # Arrange
    # Simulate projection data that includes the derived package_hash
    package_data = {
        "package_id": "PKG-HASH-TEST",
        "package_version": "v1",
        "archive_hash": "a" * 64,
        "human_record_hash": "b" * 64,
        "evidence_link_hash": "c" * 64,
        "package_status": "PACKAGE_VERIFIED",
        "reason_codes": ("OK",),
        "package_hash": "some-derived-hash", # This should be stripped
    }
    
    # Act
    from unittest.mock import patch
    from src.services.governance.promotion_governance.evidence_package_provider import EvidencePackageProvider
    from src.services.governance.promotion_governance.evidence_package_readiness_provider import EvidencePackageReadinessProvider
    
    with patch.object(EvidencePackageProvider, 'get_evidence_package_projection') as mock_proj:
        from src.services.governance.promotion_governance.evidence_package_provider import EvidencePackageResponse
        mock_proj.return_value = EvidencePackageResponse(package=package_data)
        result = EvidencePackageReadinessProvider.get_readiness_projection()
        
        # Assert
        assert result.report["package_id"] == "PKG-HASH-TEST"

