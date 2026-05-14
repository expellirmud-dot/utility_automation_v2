import pytest
from dataclasses import dataclass
from typing import List, Optional

from src.services.governance.certification.models import (
    CertificationArtifact,
    CertificationResult,
    CertificationCheck,
    CertificationFailure,
)
from src.services.governance.promotion_governance.promotion_gatekeeper import PromotionGatekeeperEvaluator
from src.services.governance.promotion_governance.gatekeeper_models import PromotionGatekeeperReport

def create_mock_artifact(
    passed_checks: List[str], 
    failed_checks: List[str] = None, 
    extra_checks: List[str] = None,
    overall_passed: bool = True,
    artifact_hash: str = "hash-123"
) -> CertificationArtifact:
    """Helper to create a certification artifact for testing."""
    results = []
    
    # Passed checks
    for i, key in enumerate(passed_checks):
        results.append(CertificationResult(
            check=CertificationCheck(
                key=key, 
                category="test", 
                description=f"Check {key}", 
                stable_order=i
            ),
            passed=True,
            failure=None
        ))
    
    # Failed checks
    if failed_checks:
        for i, key in enumerate(failed_checks):
            results.append(CertificationResult(
                check=CertificationCheck(
                    key=key, 
                    category="test", 
                    description=f"Check {key}", 
                    stable_order=len(passed_checks) + i
                ),
                passed=False,
                failure=CertificationFailure(
                    check_key=key, 
                    reason="FAILED", 
                    detail="Failure detail"
                )
            ))
            
    # Extra checks
    if extra_checks:
        for i, key in enumerate(extra_checks):
            results.append(CertificationResult(
                check=CertificationCheck(
                    key=key, 
                    category="test", 
                    description=f"Check {key}", 
                    stable_order=len(passed_checks) + (len(failed_checks) if failed_checks else 0) + i
                ),
                passed=True,
                failure=None
            ))
            
    # Ensure canonical ordering for CertificationArtifact
    results.sort(key=lambda r: r.check.stable_order)
    
    return CertificationArtifact(
        results=tuple(results),
        metadata={"artifact_hash": artifact_hash}
    )

def test_gatekeeper_pass():
    """Test case: All required checks present and passed."""
    required = PromotionGatekeeperEvaluator.REQUIRED_CHECKS
    artifact = create_mock_artifact(passed_checks=list(required))
    
    report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    assert report.passed is True
    assert report.advisory_decision == "ELIGIBLE_FOR_PROMOTION_REVIEW"
    assert len(report.failed_required_checks) == 0
    assert len(report.missing_required_checks) == 0

def test_gatekeeper_fail_failed_check():
    """Test case: One required check fails."""
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    fail_key = required.pop(0)
    
    artifact = create_mock_artifact(
        passed_checks=required,
        failed_checks=[fail_key],
        overall_passed=False
    )
    
    report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    assert report.passed is False
    assert report.advisory_decision == "BLOCKED_REQUIRED_CHECK_FAILED"
    assert fail_key in report.failed_required_checks
    assert len(report.missing_required_checks) == 0

def test_gatekeeper_fail_missing_check():
    """Test case: One required check is missing."""
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    missing_key = required.pop(0)
    
    artifact = create_mock_artifact(
        passed_checks=required,
        overall_passed=True # Artifact might say it passed overall, but gatekeeper should fail closed
    )
    
    report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    assert report.passed is False
    assert report.advisory_decision == "BLOCKED_REQUIRED_CHECK_MISSING"
    assert missing_key in report.missing_required_checks
    assert len(report.failed_required_checks) == 0

def test_gatekeeper_unknown_checks():
    """Test case: Artifact contains extra checks; they don't affect pass/fail."""
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    extra = ["unexpected_check_1", "unexpected_check_2"]
    
    artifact = create_mock_artifact(
        passed_checks=required,
        extra_checks=extra
    )
    
    report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    assert report.passed is True
    assert report.advisory_decision == "ELIGIBLE_FOR_PROMOTION_REVIEW"
    assert tuple(sorted(extra)) == report.unknown_checks

def test_gatekeeper_non_canonical_ordering():
    """Test case: Ensure the report enforces sorted results/lists."""
    # Use an artifact where results are not sorted by key
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    import random
    random.shuffle(required)
    
    artifact = create_mock_artifact(passed_checks=required)
    
    # Evaluation should return a report where results are sorted
    report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    results_keys = [r.check_key for r in report.required_results]
    assert results_keys == sorted(results_keys)

def test_gatekeeper_deterministic_hash():
    """Test case: Ensure the same artifact produces the same report hash."""
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    artifact1 = create_mock_artifact(passed_checks=required)
    artifact2 = create_mock_artifact(passed_checks=required)
    
    report1 = PromotionGatekeeperEvaluator.evaluate(artifact1)
    report2 = PromotionGatekeeperEvaluator.evaluate(artifact2)
    
    assert report1.report_hash == report2.report_hash

def test_gatekeeper_different_artifacts_different_hashes():
    """Ensure different artifacts produce different hashes."""
    required = list(PromotionGatekeeperEvaluator.REQUIRED_CHECKS)
    artifact1 = create_mock_artifact(passed_checks=required)
    
    # Artifact 2 has a different hash and one failed check
    fail_key = required[0]
    remaining = required[1:]
    artifact2 = create_mock_artifact(
        passed_checks=remaining, 
        failed_checks=[fail_key],
        artifact_hash="diff-hash"
    )
    
    report1 = PromotionGatekeeperEvaluator.evaluate(artifact1)
    report2 = PromotionGatekeeperEvaluator.evaluate(artifact2)
    
    assert report1.report_hash != report2.report_hash
