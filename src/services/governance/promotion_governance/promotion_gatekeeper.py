"""
Deterministic Promotion Gatekeeper Core.

This is an advisory governance layer that evaluates certification artifacts 
against a strict set of required checks. It operates on a "fail-closed" principle.

No execution authority. Governance visibility only.
"""

from __future__ import annotations

from typing import Optional, Tuple
from src.services.governance.certification.models import CertificationArtifact
from src.services.governance.promotion_governance.gatekeeper_models import (
    GatekeeperCheckResult,
    PromotionGatekeeperReport,
    GatekeeperDecision,
)

class PromotionGatekeeperEvaluator:
    """
    Deterministically evaluates promotion eligibility based on certification artifacts.
    
    Adheres to a strict fail-closed policy for required checks.
    """

    # Hardcoded required checks for the gatekeeper
    REQUIRED_CHECKS = (
        "ledger_truth_invariant",
        "sqlite_projection_only_invariant",
        "mesh_authority_invariant",
        "ai_advisory_only_invariant",
        "mesh_determinism",
        "pytest_pass",
        "replay_determinism",
        "projection_consistency",
        "api_governance_get_only_ops",
        "frontend_governance_no_mutation_ui",
        "security_dependency_governance",
    )

    @staticmethod
    def evaluate(certification_artifact: CertificationArtifact) -> PromotionGatekeeperReport:
        """
        Evaluate the certification artifact against gatekeeper requirements.
        
        Args:
            certification_artifact: The artifact to evaluate.
            
        Returns:
            A frozen, hashable PromotionGatekeeperReport.
        """
        # Map for fast lookup: check_key -> CertificationResult
        cert_results = {r.check.key: r for r in certification_artifact.results}
        
        required_results: list[GatekeeperCheckResult] = []
        missing_required_checks: list[str] = []
        failed_required_checks: list[str] = []
        
        # 1. Evaluate required checks explicitly
        for key in PromotionGatekeeperEvaluator.REQUIRED_CHECKS:
            result = cert_results.get(key)
            if result is None:
                missing_required_checks.append(key)
                required_results.append(
                    GatekeeperCheckResult(
                        check_key=key,
                        satisfied=False,
                        reason="CHECK_MISSING",
                        detail="Required check missing from certification artifact",
                    )
                )
            elif not result.passed:
                failed_required_checks.append(key)
                required_results.append(
                    GatekeeperCheckResult(
                        check_key=key,
                        satisfied=False,
                        reason="CHECK_FAILED",
                        detail=result.failure.reason if result.failure else "Certification check failed",
                    )
                )
            else:
                required_results.append(
                    GatekeeperCheckResult(
                        check_key=key,
                        satisfied=True,
                        reason="SATISFIED",
                        detail="Certification check passed",
                    )
                )

        # 2. Identify unknown checks (present in artifact but not in REQUIRED_CHECKS)
        unknown_checks = tuple(sorted([
            key for key in cert_results if key not in PromotionGatekeeperEvaluator.REQUIRED_CHECKS
        ]))

        # 3. Determine advisory decision (fail-closed priority)
        if missing_required_checks:
            decision: GatekeeperDecision = "BLOCKED_REQUIRED_CHECK_MISSING"
            reason_codes = ("MISSING_REQUIRED_CHECKS",)
        elif failed_required_checks:
            decision: GatekeeperDecision = "BLOCKED_REQUIRED_CHECK_FAILED"
            reason_codes = ("FAILED_REQUIRED_CHECKS",)
        elif not certification_artifact.passed:
            # Even if our specific required checks passed, if the artifact as a whole 
            # is marked failed (e.g. some other non-required check failed), 
            # we should be cautious, but based on requirements, only required checks block.
            # However, the prompt mentions BLOCKED_CERTIFICATION_FAILED.
            # Let's use it if the artifact overall failed but required ones passed.
            decision: GatekeeperDecision = "BLOCKED_CERTIFICATION_FAILED"
            reason_codes = ("CERTIFICATION_OVERALL_FAILED",)
        else:
            decision: GatekeeperDecision = "ELIGIBLE_FOR_PROMOTION_REVIEW"
            reason_codes = ("ALL_REQUIRED_SATISFIED",)

        # Special case: if we had a failure, but the decision was just based on overall artifact status,
        # we check if we should override it if required ones are fine.
        # Actually, if failed_required_checks is empty and missing_required_checks is empty, 
        # but certification_artifact.passed is False, it means some optional check failed.
        # The requirements say: "Unknown extra check = must not affect pass/fail".
        # So if all required passed, it's ELIGIBLE regardless of artifact.passed.
        
        if not missing_required_checks and not failed_required_checks:
            decision = "ELIGIBLE_FOR_PROMOTION_REVIEW"
            reason_codes = ("ALL_REQUIRED_SATISFIED",)

        return PromotionGatekeeperReport(
            passed=len(failed_required_checks) == 0 and len(missing_required_checks) == 0,
            required_results=tuple(sorted(required_results, key=lambda r: r.check_key)),
            missing_required_checks=tuple(sorted(missing_required_checks)),
            failed_required_checks=tuple(sorted(failed_required_checks)),
            unknown_checks=unknown_checks,
            advisory_decision=decision,
            reason_codes=tuple(sorted(reason_codes)),
            source_certification_hash=certification_artifact.artifact_hash,
        )
