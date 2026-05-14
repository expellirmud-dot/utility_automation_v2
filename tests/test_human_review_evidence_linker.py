import pytest
from src.services.governance.promotion_governance.evidence_linker import HumanReviewEvidenceLinker
from src.services.governance.promotion_governance.evidence_linker_models import HumanReviewEvidenceLink
from src.services.governance.promotion_governance.archive_models import ReleaseGovernanceArchive, ReleaseGovernanceEvidenceRef
from src.services.governance.promotion_governance.human_auth_models import HumanAuthorizationRecord

def create_mock_archive(archive_hash_override=None):
    # Minimal valid archive
    ref = ReleaseGovernanceEvidenceRef(stage="certification", artifact_type="T", artifact_hash="H1")
    archive = ReleaseGovernanceArchive(
        release_id="rel-1",
        certification_artifact_hash="H1",
        gatekeeper_report_hash="H2",
        authorization_hash="H3",
        advisory_decision="D",
        passed=True,
        reason_codes=(),
        evidence_chain=(ref,),
    )
    # Since archive_hash is a property based on identity_payload, we can't just override it.
    # In a real test we might use a mock or a specific set of inputs to get a target hash.
    return archive

def create_mock_record(archive_hash: str):
    return HumanAuthorizationRecord(
        archive_hash=archive_hash,
        authorizer_id="user-1",
        review_intent="REVIEW_INTENT_APPROVE",
        rationale="Stable",
        authorization_epoch=1,
        authorization_seq=0,
    )

def test_verified_link_creation():
    """Test that matching archive hashes produce a verified link."""
    archive = create_mock_archive()
    record = create_mock_record(archive.archive_hash)
    
    link = HumanReviewEvidenceLinker.create_link(record, archive)
    
    assert link.link_status == "LINK_VERIFIED"
    assert "LINK_VERIFIED" in link.reason_codes
    assert link.archive_hash == archive.archive_hash
    assert link.record_archive_hash == record.archive_hash
    assert link.record_hash == record.record_hash

def test_blocked_link_on_mismatch():
    """Test that mismatching archive hashes produce a blocked link."""
    archive = create_mock_archive()
    # Record points to a DIFFERENT archive
    record = create_mock_record("wrong-archive-hash")
    
    link = HumanReviewEvidenceLinker.create_link(record, archive)
    
    assert link.link_status == "LINK_BLOCKED_ARCHIVE_MISMATCH"
    assert "ARCHIVE_HASH_MISMATCH" in link.reason_codes
    assert link.archive_hash == archive.archive_hash
    assert link.record_archive_hash == "wrong-archive-hash"

def test_link_determinism():
    """Test that same inputs produce the same link hash."""
    archive = create_mock_archive()
    record = create_mock_record(archive.archive_hash)
    
    link1 = HumanReviewEvidenceLinker.create_link(record, archive)
    link2 = HumanReviewEvidenceLinker.create_link(record, archive)
    
    assert link1.link_hash == link2.link_hash
    assert link1.to_dict() == link2.to_dict()

def test_reason_codes_sorted_canonically():
    """Test that reason_codes are sorted in the resulting link."""
    archive = create_mock_archive()
    record = create_mock_record("wrong-hash")
    
    link = HumanReviewEvidenceLinker.create_link(record, archive)
    
    # "ARCHIVE_HASH_MISMATCH" and "LINK_BLOCKED" should be sorted
    assert link.reason_codes == tuple(sorted(("ARCHIVE_HASH_MISMATCH", "LINK_BLOCKED")))

def test_link_hash_excludes_itself():
    """Test that link_hash is not part of the identity payload."""
    archive = create_mock_archive()
    record = create_mock_record(archive.archive_hash)
    
    link = HumanReviewEvidenceLinker.create_link(record, archive)
    payload = link.identity_payload()
    
    assert "link_hash" not in payload

def test_record_archive_hash_preserved():
    """Test that the record's view of the archive hash is preserved independently."""
    archive = create_mock_archive()
    wrong_hash = "some-other-hash"
    record = create_mock_record(wrong_hash)
    
    link = HumanReviewEvidenceLinker.create_link(record, archive)
    
    assert link.archive_hash == archive.archive_hash
    assert link.record_archive_hash == wrong_hash
    assert link.archive_hash != link.record_archive_hash
