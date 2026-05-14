"""
Deterministic promotion eligibility evaluator.

Evaluates promotion eligibility based on:
- Certification artifact presence and pass status
- Security governance acknowledgment
- Invariant compliance

No execution authority. Governance visibility only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.services.governance.certification.models import CertificationArtifact

from src.services.governance.promotion_governance.promotion_models import (
    PromotionEligibility,
    PromotionEligibilityResult,
    PromotionEligibilityCriterion,
    PromotionEligibilityFailure,
)


class PromotionEligibilityEvaluator:
    """
    Deterministically evaluates promotion eligibility.
    
    No state mutations. Pure evaluation only.
    """

    # Define promotion eligibility criteria
    CRITERIA = [
        PromotionEligibilityCriterion(
            key="certification_artifact_exists",
            category="Certification",
            description="Certification artifact must exist",
            stable_order=10,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="certification_all_checks_pass",
            category="Certification",
            description="All certification checks must pass",
            stable_order=20,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="certification_score_meets_threshold",
            category="Certification",
            description="Certification score must be >= 90%",
            stable_order=30,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="ledger_truth_invariant",
            category="Governance",
            description="Ledger must be sole source of truth",
            stable_order=40,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="sqlite_projection_only_invariant",
            category="Governance",
            description="SQLite must be projection/cache only",
            stable_order=50,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="mesh_authority_invariant",
            category="Governance",
            description="Mesh quorum must be sole authority",
            stable_order=60,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="ai_advisory_only_invariant",
            category="Governance",
            description="AI must be advisory only",
            stable_order=70,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="determinism_invariant",
            category="Governance",
            description="Determinism must not weaken",
            stable_order=80,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="replay_safety_invariant",
            category="Governance",
            description="Replay safety must be maintained",
            stable_order=90,
            required=True,
        ),
        PromotionEligibilityCriterion(
            key="no_runtime_promotion_execution",
            category="Governance",
            description="No runtime promotion execution in scope",
            stable_order=100,
            required=True,
        ),
    ]

    @staticmethod
    def evaluate(
        certification_artifact: Optional[CertificationArtifact] = None,
        artifact_path: Optional[Path] = None,
    ) -> PromotionEligibility:
        """
        Deterministically evaluate promotion eligibility.

        Args:
            certification_artifact: Optional loaded CertificationArtifact
            artifact_path: Optional path to artifact JSON file

        Returns:
            PromotionEligibility with deterministic results
        """
        results = []

        # Check 1: Certification artifact exists
        artifact_exists = certification_artifact is not None or (
            artifact_path and Path(artifact_path).exists()
        )
        if artifact_exists and certification_artifact is None and artifact_path:
            # Try to load artifact
            try:
                import json

                with open(artifact_path) as f:
                    artifact_dict = json.load(f)
                # We would reconstruct CertificationArtifact here if needed
                # For now, we trust the existence check
            except Exception as e:
                artifact_exists = False

        criterion = PromotionEligibilityEvaluator.CRITERIA[0]
        if artifact_exists:
            results.append(
                PromotionEligibilityResult(
                    criterion=criterion,
                    satisfied=True,
                    failure=None,
                )
            )
        else:
            results.append(
                PromotionEligibilityResult(
                    criterion=criterion,
                    satisfied=False,
                    failure=PromotionEligibilityFailure(
                        criterion_key=criterion.key,
                        reason="Certification artifact not found",
                        detail="Expected certification_artifact.json in output/certification/",
                    ),
                )
            )

        # Build results lookup map for deterministic matching
        results_by_key: dict[str, PromotionEligibilityResult] = {} # Placeholder for real results if available
        # Actually we need a map of CertificationResult, not PromotionEligibilityResult
        # Let's use a local map for CertificationResults
        cert_results_by_key = {}
        if certification_artifact:
            cert_results_by_key = {r.check.key: r for r in certification_artifact.results}

        # Check 2: All certification checks pass
        criterion = PromotionEligibilityEvaluator.CRITERIA[1]
        if certification_artifact and certification_artifact.passed:
            results.append(
                PromotionEligibilityResult(
                    criterion=criterion,
                    satisfied=True,
                    failure=None,
                )
            )
        else:
            failure_count = len(certification_artifact.failures) if certification_artifact else 0
            results.append(
                PromotionEligibilityResult(
                    criterion=criterion,
                    satisfied=False,
                    failure=PromotionEligibilityFailure(
                        criterion_key=criterion.key,
                        reason="Certification checks failed",
                        detail=f"{failure_count} check(s) failed",
                    ),
                )
            )

        # Check 3: Certification score meets threshold
        criterion = PromotionEligibilityEvaluator.CRITERIA[2]
        if certification_artifact:
            score = certification_artifact.overall_score
            if score >= 90.0:
                results.append(
                    PromotionEligibilityResult(
                        criterion=criterion,
                        satisfied=True,
                        failure=None,
                    )
                )
            else:
                results.append(
                    PromotionEligibilityResult(
                        criterion=criterion,
                        satisfied=False,
                        failure=PromotionEligibilityFailure(
                            criterion_key=criterion.key,
                            reason="Certification score below threshold",
                            detail=f"Score: {score}%, Required: 90%",
                        ),
                    )
                )
        else:
            results.append(
                PromotionEligibilityResult(
                    criterion=criterion,
                    satisfied=False,
                    failure=PromotionEligibilityFailure(
                        criterion_key=criterion.key,
                        reason="Cannot evaluate score without artifact",
                        detail="Certification artifact required",
                    ),
                )
            )

        # Checks 4-10: Invariant compliance
        # Map each criterion key to its corresponding certification check result
        invariant_criteria = PromotionEligibilityEvaluator.CRITERIA[3:10]
        for criterion in invariant_criteria:
            cert_result = cert_results_by_key.get(criterion.key)
            if cert_result and cert_result.passed:
                results.append(
                    PromotionEligibilityResult(
                        criterion=criterion,
                        satisfied=True,
                        failure=None,
                    )
                )
            else:
                reason = "Invariant compliance not verified" if not cert_result else "Certification check failed"
                detail = "Requires passing certification" if not cert_result else f"Check {criterion.key} failed"
                results.append(
                    PromotionEligibilityResult(
                        criterion=criterion,
                        satisfied=False,
                        failure=PromotionEligibilityFailure(
                            criterion_key=criterion.key,
                            reason=reason,
                            detail=detail,
                        ),
                    )
                )

        # Create tuple in canonical order
        results_tuple = tuple(
            sorted(results, key=lambda r: r.criterion.stable_order)
        )

        return PromotionEligibility(
            results=results_tuple,
            metadata={
                "evaluator_version": "task-050-b-v1",
                "evaluation_mode": "governance-only",
            },
        )
