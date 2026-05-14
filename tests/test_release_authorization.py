import pytest
from typing import List

from src.services.governance.certification.models import (
    CertificationArtifact,
    CertificationResult,
    CertificationCheck,
    CertificationFailure,
)
from src.services.governance.promotion_governance.gatekeeper_models import (
    PromotionGatekeeperReport,
    GatekeeperCheckResult,
)
from src.services.governance.promotion_governance.release_authorizer import ReleaseAuthorizer
from src.services.governance.promotion_governance.authorization_models import ReleaseAuthorizationBundle

def create_mock_artifact(
    passed: bool = True, 
    metadata: dict = None
) -> CertificationArtifact:
    """Helper to create a basic certification artifact."""
    if metadata is None:
        metadata = {}
    
    results = []
    # Use a fixed key for consistency
    check = CertificationCheck(key="dummy", category="test", description="dummy", stable_order=0)
    
    if passed:
        results.append(CertificationResult(check=check, passed=True))
    else:
        results.append(CertificationResult(
            check=check, 
            passed=False, 
            failure=CertificationFailure(check_key="dummy", reason="FAILED", detail="Fail")
        ))
        
    return CertificationArtifact(
        results=tuple(results),
        metadata=metadata
    )

def create_mock_gatekeeper_report(
    passed: bool = True, 
    decision: str = "ELIGIBLE_FOR_PROMOTION_REVIEW",
    source_cert_hash: str = None,
) -> PromotionGatekeeperReport:
    """Helper to create a basic gatekeeper report."""
    # Use a fixed key for consistency
    results = (GatekeeperCheckResult(check_key="dummy", satisfied=passed),)
    
    return PromotionGatekeeperReport(
        passed=passed,
        required_results=results,
        missing_required_checks=(),
        failed_required_checks=(),
        unknown_checks=(),
        advisory_decision=decision,
        reason_codes=("SATISFIED",),
        source_certification_hash=source_cert_hash or "default-hash",
    )

def test_auth_success():
    """Test case: Certification and Gatekeeper both pass."""
    artifact = create_mock_artifact(passed=True)
    report = create_mock_gatekeeper_report(
        passed=True, 
        decision="ELIGIBLE_FOR_PROMOTION_REVIEW",
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle = ReleaseAuthorizer.authorize(artifact, report)
    
    assert bundle.passed is True
    assert bundle.advisory_decision == "ELIGIBLE_FOR_RELEASE_AUTHORIZATION_REVIEW"
    assert "ALL_GOVERNANCE_CRITERIA_SATISFIED" in bundle.reason_codes

def test_auth_block_certification_failed():
    """Test case: Certification fails."""
    artifact = create_mock_artifact(passed=False)
    report = create_mock_gatekeeper_report(
        passed=True, 
        decision="ELIGIBLE_FOR_PROMOTION_REVIEW",
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle = ReleaseAuthorizer.authorize(artifact, report)
    
    assert bundle.passed is False
    assert bundle.advisory_decision == "BLOCKED_CERTIFICATION_FAILED"
    assert "CERTIFICATION_FAILED" in bundle.reason_codes

def test_auth_block_gatekeeper_failed():
    """Test case: Gatekeeper failed."""
    artifact = create_mock_artifact(passed=True)
    report = create_mock_gatekeeper_report(
        passed=False, 
        decision="BLOCKED_REQUIRED_CHECK_FAILED",
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle = ReleaseAuthorizer.authorize(artifact, report)
    
    assert bundle.passed is False
    assert bundle.advisory_decision == "BLOCKED_GATEKEEPER_FAILED"
    assert "GATEKEEPER_FAILED" in bundle.reason_codes

def test_auth_block_gatekeeper_not_eligible():
    """Test case: Gatekeeper passed but decision is not eligible."""
    artifact = create_mock_artifact(passed=True)
    report = create_mock_gatekeeper_report(
        passed=True, 
        decision="BLOCKED_CERTIFICATION_FAILED",
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle = ReleaseAuthorizer.authorize(artifact, report)
    
    assert bundle.passed is False
    assert bundle.advisory_decision == "BLOCKED_GATEKEEPER_FAILED"
    assert "GATEKEEPER_NOT_ELIGIBLE" in bundle.reason_codes

def test_auth_block_input_inconsistent():
    """Test case: Certification hash mismatches gatekeeper source hash."""
    # Create two truly different artifacts
    artifact_a = create_mock_artifact(passed=True)
    
    # Artifact B has a different check result to ensure a different hash
    check_b = CertificationCheck(key="dummy-b", category="test", description="dummy-b", stable_order=0)
    result_b = CertificationResult(check=check_b, passed=True)
    artifact_b = CertificationArtifact(results=(result_b,))
    
    # Gatekeeper report points to artifact A
    report = create_mock_gatekeeper_report(
        passed=True,
        decision="ELIGIBLE_FOR_PROMOTION_REVIEW",
        source_cert_hash=artifact_a.artifact_hash
    )
    
    # But we pass artifact B to the authorizer
    bundle = ReleaseAuthorizer.authorize(artifact_b, report)
    
    assert bundle.passed is False
    assert bundle.advisory_decision == "BLOCKED_INPUT_INCONSISTENT"
    assert "INPUT_HASH_MISMATCH" in bundle.reason_codes

def test_auth_deterministic_hash():
    """Test case: Stable hash for same inputs."""
    artifact = create_mock_artifact(passed=True)
    report = create_mock_gatekeeper_report(
        passed=True, 
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle1 = ReleaseAuthorizer.authorize(artifact, report)
    bundle2 = ReleaseAuthorizer.authorize(artifact, report)
    
    assert bundle1.authorization_hash == bundle2.authorization_hash

def test_auth_canonical_ordering():
    """Test case: Reason codes are sorted."""
    artifact = create_mock_artifact(passed=True)
    # Trigger both GATEKEEPER_FAILED and GATEKEEPER_NOT_ELIGIBLE
    report = create_mock_gatekeeper_report(
        passed=False, 
        decision="BLOCKED_REQUIRED_CHECK_FAILED",
        source_cert_hash=artifact.artifact_hash
    )
    
    bundle = ReleaseAuthorizer.authorize(artifact, report)
    assert bundle.reason_codes == tuple(sorted(bundle.reason_codes))
