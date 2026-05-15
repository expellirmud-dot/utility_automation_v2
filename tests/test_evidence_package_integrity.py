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

def test_validate_package_success(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    report = EvidencePackageIntegrityGate.validate_package(package, version)
    assert report.passed is True
    assert len(report.violations) == 0

def test_validate_package_wrong_version(mock_archive, mock_human_record, verified_link):
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    report = EvidencePackageIntegrityGate.validate_package(package, "wrong-version-v0")
    assert report.passed is False
    assert any(v.field == "package_version" for v in report.violations)

def test_validate_payload_success(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    payload = package.to_dict()
    report = EvidencePackageIntegrityGate.validate_payload(payload, version)
    assert report.passed is True
    assert len(report.violations) == 0

def test_validate_payload_hash_mismatch(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    payload = package.to_dict()
    payload["package_hash"] = "incorrect-hash-value"
    
    report = EvidencePackageIntegrityGate.validate_payload(payload, version)
    assert report.passed is False
    assert any(v.field == "package_hash" for v in report.violations)
    assert "Hash mismatch" in report.violations[0].reason

def test_validate_payload_missing_field(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    payload = package.to_dict()
    del payload["archive_hash"]
    
    report = EvidencePackageIntegrityGate.validate_payload(payload, version)
    assert report.passed is False
    assert any(v.field == "archive_hash" for v in report.violations)

def test_validate_payload_unsorted_reasons(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    # Manually create an unsorted payload
    payload = {
        "package_id": "PKG-001",
        "package_version": version,
        "archive_hash": "h1",
        "human_record_hash": "h2",
        "evidence_link_hash": "h3",
        "package_status": "PACKAGE_VERIFIED",
        "reason_codes": ["Z", "A"], # Unsorted
        "package_hash": "some-hash" # This will also cause a hash mismatch, but we check reasons
    }
    # Recalculate hash so we only see the sorted violation if possible, 
    # or just check that sorted violation is present.
    
    report = EvidencePackageIntegrityGate.validate_payload(payload, version)
    assert report.passed is False
    assert any(v.field == "reason_codes" for v in report.violations)

def test_report_determinism(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    
    report1 = EvidencePackageIntegrityGate.validate_package(package, version)
    report2 = EvidencePackageIntegrityGate.validate_package(package, version)
    
    assert report1.report_hash == report2.report_hash
    assert report1.to_dict() == report2.to_dict()

def test_payload_bad_status(mock_archive, mock_human_record, verified_link):
    version = GovernanceEvidencePackageCreator.PACKAGE_VERSION
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    payload = package.to_dict()
    payload["package_status"] = "SUPER_VERIFIED"
    
    report = EvidencePackageIntegrityGate.validate_payload(payload, version)
    assert report.passed is False
    assert any(v.field == "package_status" for v in report.violations)
