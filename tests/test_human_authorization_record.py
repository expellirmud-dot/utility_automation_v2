import pytest
from src.services.governance.promotion_governance.human_auth_models import (
    HumanAuthorizationRecord,
    HumanAuthorizationSummary,
)
from src.services.governance.promotion_governance.human_auth_recorder import HumanAuthRecorder

def test_stable_record_creation():
    """Test that same inputs produce the same record hash."""
    params = {
        "archive_hash": "hash123",
        "authorizer_id": "user-1",
        "review_intent": "REVIEW_INTENT_APPROVE",
        "rationale": "All checks passed",
        "authorization_epoch": 1,
        "authorization_seq": 0,
    }
    
    record1 = HumanAuthRecorder.record_intent(**params)
    record2 = HumanAuthRecorder.record_intent(**params)
    
    assert record1.record_hash == record2.record_hash
    assert record1.to_dict() == record2.to_dict()

def test_invalid_review_intent():
    """Test that invalid intent values are rejected."""
    with pytest.raises(ValueError, match="Invalid review_intent"):
        HumanAuthRecorder.record_intent(
            archive_hash="hash123",
            authorizer_id="user-1",
            review_intent="AUTHORIZED",  # Invalid terminology
            rationale="Wrong term",
            authorization_epoch=1,
            authorization_seq=0,
        )

def test_missing_archive_hash():
    """Test that missing archive_hash is rejected."""
    with pytest.raises(ValueError, match="archive_hash is required"):
        HumanAuthRecorder.record_intent(
            archive_hash="",
            authorizer_id="user-1",
            review_intent="REVIEW_INTENT_APPROVE",
            rationale="No hash",
            authorization_epoch=1,
            authorization_seq=0,
        )

def test_missing_authorizer_id():
    """Test that missing authorizer_id is rejected."""
    with pytest.raises(ValueError, match="authorizer_id is required"):
        HumanAuthRecorder.record_intent(
            archive_hash="hash123",
            authorizer_id="",
            review_intent="REVIEW_INTENT_APPROVE",
            rationale="No user",
            authorization_epoch=1,
            authorization_seq=0,
        )

def test_negative_epoch_seq():
    """Test that negative epoch or sequence is rejected."""
    with pytest.raises(ValueError, match="authorization_epoch must be >= 0"):
        HumanAuthRecorder.record_intent(
            archive_hash="hash123",
            authorizer_id="user-1",
            review_intent="REVIEW_INTENT_APPROVE",
            rationale="Negative epoch",
            authorization_epoch=-1,
            authorization_seq=0,
        )
        
    with pytest.raises(ValueError, match="authorization_seq must be >= 0"):
        HumanAuthRecorder.record_intent(
            archive_hash="hash123",
            authorizer_id="user-1",
            review_intent="REVIEW_INTENT_APPROVE",
            rationale="Negative seq",
            authorization_epoch=1,
            authorization_seq=-1,
        )

def test_changed_rationale_changes_hash():
    """Test that changing the rationale changes the record hash."""
    base_params = {
        "archive_hash": "hash123",
        "authorizer_id": "user-1",
        "review_intent": "REVIEW_INTENT_APPROVE",
        "rationale": "Rationale A",
        "authorization_epoch": 1,
        "authorization_seq": 0,
    }
    
    record1 = HumanAuthRecorder.record_intent(**base_params)
    
    params2 = base_params.copy()
    params2["rationale"] = "Rationale B"
    record2 = HumanAuthRecorder.record_intent(**params2)
    
    assert record1.record_hash != record2.record_hash

def test_record_hash_excludes_itself():
    """Test that record_hash is not part of the identity payload."""
    record = HumanAuthRecorder.record_intent(
        archive_hash="hash123",
        authorizer_id="user-1",
        review_intent="REVIEW_INTENT_APPROVE",
        rationale="Stable",
        authorization_epoch=1,
        authorization_seq=0,
    )
    payload = record.identity_payload()
    assert "record_hash" not in payload

def test_summary_is_deterministic():
    """Test that the summary model is deterministic."""
    record = HumanAuthRecorder.record_intent(
        archive_hash="hash123",
        authorizer_id="user-1",
        review_intent="REVIEW_INTENT_APPROVE",
        rationale="Detailed rationale",
        authorization_epoch=1,
        authorization_seq=0,
    )
    
    summary1 = HumanAuthRecorder.create_summary(record)
    summary2 = HumanAuthRecorder.create_summary(record)
    
    assert summary1.to_dict() == summary2.to_dict()
    assert summary1.record_hash == record.record_hash
