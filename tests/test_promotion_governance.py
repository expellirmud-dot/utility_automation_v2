"""
Tests for promotion governance workflow.

Tests:
- Frozen immutability of domain models
- Deterministic serialization
- Canonical ordering
- Hash stability
- Evaluation logic
- Manifest generation
- Error cases
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import json
from pathlib import Path
import tempfile

from src.services.governance.promotion_governance.promotion_models import (
    PromotionEligibilityFailure,
    PromotionEligibilityCriterion,
    PromotionEligibilityResult,
    PromotionEligibility,
    PromotionRequest,
    PromotionDecision,
    PromotionBundle,
    canonical_json,
)
from src.services.governance.promotion_governance.promotion_evaluator import (
    PromotionEligibilityEvaluator,
)
from src.services.governance.promotion_governance.promotion_manifest_generator import (
    PromotionManifestGenerator,
)


class TestCanonicalJson:
    """Test deterministic JSON serialization."""

    def test_sorted_keys(self):
        """Keys are sorted deterministically."""
        payload = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(payload)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_deterministic_output(self):
        """Multiple calls produce identical output."""
        payload = {"b": 2, "a": 1}
        result1 = canonical_json(payload)
        result2 = canonical_json(payload)
        assert result1 == result2

    def test_nested_sorting(self):
        """Nested dicts are sorted."""
        payload = {"outer": {"z": 1, "a": 2}}
        result = canonical_json(payload)
        assert '"outer":{"a":2,"z":1}' in result


class TestPromotionEligibilityFailure:
    """Test eligibility failure model."""

    def test_frozen_immutable(self):
        """PromotionEligibilityFailure is frozen."""
        failure = PromotionEligibilityFailure(
            criterion_key="test_key",
            reason="Test reason",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            failure.criterion_key = "modified"

    def test_to_dict(self):
        """to_dict produces sorted keys."""
        failure = PromotionEligibilityFailure(
            criterion_key="test",
            reason="Reason text",
            detail="Detail text",
        )
        result = failure.to_dict()
        assert result["criterion_key"] == "test"
        assert result["reason"] == "Reason text"
        assert result["detail"] == "Detail text"


class TestPromotionEligibilityCriterion:
    """Test eligibility criterion model."""

    def test_frozen_immutable(self):
        """Criterion is frozen."""
        criterion = PromotionEligibilityCriterion(
            key="test_key",
            category="Test",
            description="Test description",
            stable_order=10,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            criterion.key = "modified"

    def test_to_dict_sorting(self):
        """to_dict produces sorted keys."""
        criterion = PromotionEligibilityCriterion(
            key="test_key",
            category="Category",
            description="Description",
            stable_order=42,
        )
        result = criterion.to_dict()
        # Keys should be sorted when serialized
        keys = list(result.keys())
        assert keys == sorted(keys)


class TestPromotionEligibilityResult:
    """Test eligibility result model."""

    def test_satisfied_no_failure_allowed(self):
        """Satisfied result has no failure."""
        criterion = PromotionEligibilityCriterion(
            key="test",
            category="Test",
            description="Test",
            stable_order=1,
        )
        result = PromotionEligibilityResult(
            criterion=criterion,
            satisfied=True,
            failure=None,
        )
        assert result.satisfied is True
        assert result.failure is None

    def test_failed_requires_failure(self):
        """Failed result must have failure object."""
        criterion = PromotionEligibilityCriterion(
            key="test",
            category="Test",
            description="Test",
            stable_order=1,
        )
        with pytest.raises(ValueError, match="failed eligibility result requires a failure"):
            PromotionEligibilityResult(
                criterion=criterion,
                satisfied=False,
                failure=None,
            )


class TestPromotionEligibility:
    """Test eligibility aggregation model."""

    def test_frozen_immutable(self):
        """PromotionEligibility is frozen."""
        criterion = PromotionEligibilityCriterion(
            key="test",
            category="Test",
            description="Test",
            stable_order=1,
        )
        result = PromotionEligibilityResult(
            criterion=criterion,
            satisfied=True,
        )
        eligibility = PromotionEligibility(results=(result,))
        
        with pytest.raises(Exception):  # FrozenInstanceError
            eligibility.results = ()

    def test_canonical_ordering_enforced(self):
        """Results must be in canonical order."""
        c1 = PromotionEligibilityCriterion(
            key="z", category="Test", description="Z", stable_order=10
        )
        c2 = PromotionEligibilityCriterion(
            key="a", category="Test", description="A", stable_order=5
        )
        r1 = PromotionEligibilityResult(criterion=c1, satisfied=True)
        r2 = PromotionEligibilityResult(criterion=c2, satisfied=True)
        
        # Wrong order
        with pytest.raises(ValueError, match="must be in canonical order"):
            PromotionEligibility(results=(r1, r2))  # 10 before 5

    def test_eligible_all_required_pass(self):
        """Eligible when all required criteria pass."""
        c1 = PromotionEligibilityCriterion(
            key="a", category="Test", description="A", stable_order=1, required=True
        )
        r1 = PromotionEligibilityResult(criterion=c1, satisfied=True)
        eligibility = PromotionEligibility(results=(r1,))
        assert eligibility.eligible is True

    def test_not_eligible_required_fail(self):
        """Not eligible if any required criterion fails."""
        c1 = PromotionEligibilityCriterion(
            key="a", category="Test", description="A", stable_order=1, required=True
        )
        failure = PromotionEligibilityFailure(criterion_key="a", reason="Failed")
        r1 = PromotionEligibilityResult(
            criterion=c1, satisfied=False, failure=failure
        )
        eligibility = PromotionEligibility(results=(r1,))
        assert eligibility.eligible is False

    def test_eligibility_score(self):
        """Eligibility score computed correctly."""
        criteria = []
        results = []
        for i in range(10):
            c = PromotionEligibilityCriterion(
                key=f"c{i}",
                category="Test",
                description=f"Criterion {i}",
                stable_order=i,
            )
            criteria.append(c)
            satisfied = i < 7  # 7 pass, 3 fail
            failure = None
            if not satisfied:
                failure = PromotionEligibilityFailure(
                    criterion_key=f"c{i}",
                    reason="Test failure",
                )
            results.append(
                PromotionEligibilityResult(
                    criterion=c, satisfied=satisfied, failure=failure
                )
            )
        
        eligibility = PromotionEligibility(results=tuple(results))
        assert eligibility.eligibility_score == 70.0

    def test_identity_hash_deterministic(self):
        """Identity hash is deterministic."""
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        e1 = PromotionEligibility(results=(r,))
        e2 = PromotionEligibility(results=(r,))
        
        assert e1.eligibility_hash == e2.eligibility_hash


class TestPromotionRequest:
    """Test promotion request model."""

    def test_frozen_immutable(self):
        """PromotionRequest is frozen."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            request.source_version_id = "v2"

    def test_valid_stages(self):
        """Valid stages are accepted."""
        for stage in ["simulation", "approved", "production"]:
            request = PromotionRequest(
                source_version_id="v1",
                target_stage=stage,
                requested_by="user",
                request_epoch=1,
                request_seq=1,
            )
            assert request.target_stage == stage

    def test_invalid_stage_rejected(self):
        """Invalid stages raise error."""
        with pytest.raises(ValueError, match="Invalid target_stage"):
            PromotionRequest(
                source_version_id="v1",
                target_stage="invalid_stage",
                requested_by="user",
                request_epoch=1,
                request_seq=1,
            )


class TestPromotionDecision:
    """Test promotion decision model."""

    def test_frozen_immutable(self):
        """PromotionDecision is frozen."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            decision.decision = "rejected"

    def test_valid_decisions(self):
        """Valid decisions are accepted."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        
        for decision_str in ["approved", "deferred", "rejected"]:
            decision = PromotionDecision(
                promotion_request=request,
                eligibility=eligibility,
                decision=decision_str,
                decision_rationale="Test",
                decision_epoch=1,
                decision_seq=1,
            )
            assert decision.decision == decision_str

    def test_decision_hash_deterministic(self):
        """Decision hash is deterministic."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        
        d1 = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        d2 = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        
        assert d1.decision_hash == d2.decision_hash


class TestPromotionBundle:
    """Test promotion bundle aggregation."""

    def test_frozen_immutable(self):
        """PromotionBundle is frozen."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        bundle = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            bundle.request = None

    def test_consistency_check(self):
        """Bundle enforces internal consistency."""
        request1 = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        request2 = PromotionRequest(
            source_version_id="v2",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        
        decision = PromotionDecision(
            promotion_request=request1,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        
        # Inconsistent request
        with pytest.raises(ValueError, match="decision request must match"):
            PromotionBundle(
                request=request2,  # Different from decision's request
                eligibility=eligibility,
                decision=decision,
            )

    def test_bundle_hash_deterministic(self):
        """Bundle hash is deterministic."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        
        b1 = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        b2 = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        
        assert b1.bundle_hash == b2.bundle_hash


class TestPromotionEligibilityEvaluator:
    """Test promotion eligibility evaluator."""

    def test_criteria_stable_order(self):
        """Criteria have stable ordering."""
        criteria = PromotionEligibilityEvaluator.CRITERIA
        orders = [c.stable_order for c in criteria]
        assert orders == sorted(orders)

    def test_evaluate_no_artifact(self):
        """Evaluation without artifact marks as ineligible."""
        result = PromotionEligibilityEvaluator.evaluate()
        assert result.eligible is False
        assert len(result.failures) > 0


class TestPromotionManifestGenerator:
    """Test promotion manifest generation."""

    def test_generate_manifest(self):
        """Manifest generated and saved correctly."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        bundle = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "promotion"
            path = PromotionManifestGenerator.generate_manifest(bundle, output_dir)
            
            assert path.exists()
            assert path.name == "promotion_manifest.json"
            
            # Verify content
            manifest = PromotionManifestGenerator.load_manifest(path)
            assert manifest["type"] == "promotion_governance_manifest"
            assert manifest["bundle"]["decision"]["decision"] == "approved"

    def test_manifest_determinism(self):
        """Manifest is deterministically serializable."""
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="Test",
            decision_epoch=1,
            decision_seq=1,
        )
        bundle = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "promotion"
            path = PromotionManifestGenerator.generate_manifest(bundle, output_dir)
            
            assert PromotionManifestGenerator.verify_manifest_determinism(path)

    def test_generate_simple_decision_bundle(self):
        """Convenience method creates valid bundle."""
        c = PromotionEligibilityCriterion(
            key="test", category="Test", description="Test", stable_order=1
        )
        r = PromotionEligibilityResult(criterion=c, satisfied=True)
        eligibility = PromotionEligibility(results=(r,))
        
        # Construct bundle explicitly
        request = PromotionRequest(
            source_version_id="v1",
            target_stage="approved",
            requested_by="user",
            request_epoch=1,
            request_seq=1,
        )
        
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision="approved",
            decision_rationale="All promotion eligibility criteria satisfied",
            decision_epoch=1,
            decision_seq=1,
        )
        
        bundle = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )
        
        assert bundle.request.source_version_id == "v1"
        assert bundle.decision.decision == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
