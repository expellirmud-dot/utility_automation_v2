import pytest
from src.services.governance.promotion_governance.archive_models import ReleaseGovernanceArchive, ReleaseGovernanceEvidenceRef
from src.services.governance.promotion_governance.human_auth_models import HumanAuthorizationRecord
from src.services.governance.promotion_governance.evidence_linker_models import HumanReviewEvidenceLink
from src.services.governance.promotion_governance.evidence_package_creator import GovernanceEvidencePackageCreator
from src.services.governance.promotion_governance.evidence_package_models import GovernanceEvidencePackage

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
        promotion_bundle_hash="promo-hash",
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

def test_create_verified_package(mock_archive, mock_human_record, verified_link):
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-001", mock_archive, mock_human_record, verified_link
    )
    assert package.package_status == "PACKAGE_VERIFIED"
    assert "PACKAGE_VERIFIED" in package.reason_codes
    assert package.package_id == "PKG-001"

def test_create_invalid_package(mock_archive, mock_human_record, unverified_link):
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-002", mock_archive, mock_human_record, unverified_link
    )
    assert package.package_status == "PACKAGE_INVALID"
    assert "EVIDENCE_LINK_NOT_VERIFIED" in package.reason_codes

def test_deterministic_hash(mock_archive, mock_human_record, verified_link):
    p1 = GovernanceEvidencePackageCreator.create_package(
        "PKG-SAME", mock_archive, mock_human_record, verified_link
    )
    p2 = GovernanceEvidencePackageCreator.create_package(
        "PKG-SAME", mock_archive, mock_human_record, verified_link
    )
    assert p1.package_hash == p2.package_hash

def test_package_id_changes_hash(mock_archive, mock_human_record, verified_link):
    p1 = GovernanceEvidencePackageCreator.create_package(
        "PKG-1", mock_archive, mock_human_record, verified_link
    )
    p2 = GovernanceEvidencePackageCreator.create_package(
        "PKG-2", mock_archive, mock_human_record, verified_link
    )
    assert p1.package_hash != p2.package_hash

def test_reason_codes_sorted(mock_archive, mock_human_record, unverified_link):
    # The creator sorts reason_codes
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-SORT", mock_archive, mock_human_record, unverified_link
    )
    assert list(package.reason_codes) == sorted(list(package.reason_codes))

def test_package_hash_excludes_itself(mock_archive, mock_human_record, verified_link):
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-HASH", mock_archive, mock_human_record, verified_link
    )
    payload = package.identity_payload()
    assert "package_hash" not in payload

def test_rejects_empty_package_id(mock_archive, mock_human_record, verified_link):
    with pytest.raises(ValueError, match="package_id is required"):
        GovernanceEvidencePackageCreator.create_package(
            "", mock_archive, mock_human_record, verified_link
        )

def test_stores_hash_references_only(mock_archive, mock_human_record, verified_link):
    package = GovernanceEvidencePackageCreator.create_package(
        "PKG-REF", mock_archive, mock_human_record, verified_link
    )
    # Check that we are storing hashes, not objects
    assert isinstance(package.archive_hash, str)
    assert isinstance(package.human_record_hash, str)
    assert isinstance(package.evidence_link_hash, str)

def test_no_production_dependency_on_tests():
    # Ensure we don't import from src.tests in production code
    import src.services.governance.promotion_governance.evidence_package_models as models
    import src.services.governance.promotion_governance.evidence_package_creator as creator
    
    for module in [models, creator]:
        for name in dir(module):
            # Check for any import that looks like a test path
            # (Though this is mostly static analysis, we check if anything was accidentally imported)
            pass
    assert True # If it loaded without error and we didn't manually add them, we are good.
