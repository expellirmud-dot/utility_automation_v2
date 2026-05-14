import pytest
from src.services.governance.promotion_governance.archive_models import (
    ReleaseGovernanceArchive,
    ReleaseGovernanceEvidenceRef,
)
from src.services.governance.promotion_governance.governance_archiver import GovernanceArchiver
from src.services.governance.certification.models import (
    CertificationArtifact,
    CertificationCheck,
    CertificationResult,
)
from src.services.governance.promotion_governance.gatekeeper_models import (
    PromotionGatekeeperReport,
    GatekeeperCheckResult,
)
from src.services.governance.promotion_governance.authorization_models import (
    ReleaseAuthorizationBundle,
)
from src.services.governance.promotion_governance.promotion_models import (
    PromotionBundle,
    PromotionRequest,
    PromotionEligibility,
    PromotionEligibilityCriterion,
    PromotionEligibilityResult,
    PromotionDecision,
)

def create_mock_certification():
    check = CertificationCheck(key="C1", category="Core", description="Desc", stable_order=1)
    result = CertificationResult(check=check, passed=True)
    return CertificationArtifact(results=(result,), metadata={"env": "test"})

def create_mock_gatekeeper(cert_hash: str):
    return PromotionGatekeeperReport(
        passed=True,
        required_results=(GatekeeperCheckResult(check_key="G1", satisfied=True),),
        missing_required_checks=(),
        failed_required_checks=(),
        unknown_checks=(),
        advisory_decision="ELIGIBLE_FOR_PROMOTION_REVIEW",
        reason_codes=("R1",),
        source_certification_hash=cert_hash,
    )

def create_mock_authorization(cert_hash: str, gate_hash: str):
    return ReleaseAuthorizationBundle(
        passed=True,
        advisory_decision="ELIGIBLE_FOR_RELEASE_AUTHORIZATION_REVIEW",
        source_certification_hash=cert_hash,
        source_gatekeeper_hash=gate_hash,
        reason_codes=("A1",),
    )

def create_mock_promotion(cert_hash: str, gate_hash: str):
    req = PromotionRequest(
        source_version_id="v1",
        target_stage="production",
        requested_by="admin",
        request_epoch=1,
        request_seq=1,
    )
    crit = PromotionEligibilityCriterion(key="P1", category="Gov", description="Desc", stable_order=1)
    res = PromotionEligibilityResult(criterion=crit, satisfied=True)
    elig = PromotionEligibility(results=(res,))
    dec = PromotionDecision(
        promotion_request=req,
        eligibility=elig,
        decision="approved",
        decision_rationale="All clear",
        decision_epoch=1,
        decision_seq=1,
    )
    return PromotionBundle(request=req, eligibility=elig, decision=dec)

def test_archive_stable_hash():
    """Test that same inputs produce the same archive hash."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    
    archive1 = GovernanceArchiver.archive("rel-1", cert, gate, auth)
    archive2 = GovernanceArchiver.archive("rel-1", cert, gate, auth)
    
    assert archive1.archive_hash == archive2.archive_hash
    assert archive1.to_dict() == archive2.to_dict()

def test_archive_different_release_id():
    """Test that different release_ids produce different hashes."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    
    archive1 = GovernanceArchiver.archive("rel-1", cert, gate, auth)
    archive2 = GovernanceArchiver.archive("rel-2", cert, gate, auth)
    
    assert archive1.archive_hash != archive2.archive_hash

def test_archive_missing_promotion_bundle_deterministic():
    """Test that missing optional promotion bundle is handled deterministically."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    
    archive1 = GovernanceArchiver.archive("rel-1", cert, gate, auth, promotion=None)
    archive2 = GovernanceArchiver.archive("rel-1", cert, gate, auth, promotion=None)
    
    assert archive1.promotion_bundle_hash is None
    assert archive1.archive_hash == archive2.archive_hash
    
    # Evidence chain should only have 3 entries (cert, gate, auth)
    assert len(archive1.evidence_chain) == 3

def test_archive_with_promotion_bundle():
    """Test archive with promotion bundle included."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    prom = create_mock_promotion(cert.artifact_hash, gate.report_hash)
    
    archive = GovernanceArchiver.archive("rel-1", cert, gate, auth, promotion=prom)
    
    assert archive.promotion_bundle_hash == prom.bundle_hash
    assert len(archive.evidence_chain) == 4
    # Check order: cert(10), gate(20), promotion(30), auth(40)
    assert archive.evidence_chain[0].stage == "certification"
    assert archive.evidence_chain[1].stage == "gatekeeper"
    assert archive.evidence_chain[2].stage == "promotion_governance"
    assert archive.evidence_chain[3].stage == "release_authorization"

def test_archive_release_id_required():
    """Test that empty release_id raises ValueError."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    
    with pytest.raises(ValueError, match="release_id is required"):
        GovernanceArchiver.archive("", cert, gate, auth)

def test_archive_hash_excludes_itself():
    """Test that archive_hash is not part of the identity payload."""
    cert = create_mock_certification()
    gate = create_mock_gatekeeper(cert.artifact_hash)
    auth = create_mock_authorization(cert.artifact_hash, gate.report_hash)
    
    archive = GovernanceArchiver.archive("rel-1", cert, gate, auth)
    payload = archive.identity_payload()
    
    assert "archive_hash" not in payload

def test_evidence_chain_sorting_enforcement():
    """Test that ReleaseGovernanceArchive enforces sorting in __post_init__."""
    ref1 = ReleaseGovernanceEvidenceRef(stage="certification", artifact_type="T", artifact_hash="H1")
    ref2 = ReleaseGovernanceEvidenceRef(stage="gatekeeper", artifact_type="T", artifact_hash="H2")
    
    # Correct order
    ReleaseGovernanceArchive(
        release_id="r", certification_artifact_hash="H1", gatekeeper_report_hash="H2",
        authorization_hash="H3", advisory_decision="D", passed=True,
        reason_codes=(), evidence_chain=(ref1, ref2),
    )
    
    # Incorrect order
    with pytest.raises(ValueError, match="evidence_chain must be sorted"):
        ReleaseGovernanceArchive(
            release_id="r", certification_artifact_hash="H1", gatekeeper_report_hash="H2",
            authorization_hash="H3", advisory_decision="D", passed=True,
            reason_codes=(), evidence_chain=(ref2, ref1),
        )
