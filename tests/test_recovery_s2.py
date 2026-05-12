"""
TASK 039-S2: Recovery Classifier + Plan Builder Tests.

Verifies:
1. Classifier determinism: identical signal → identical diagnosis
2. Plan builder determinism: identical diagnosis → identical plan
3. All 7 taxonomy values are covered
4. All S1 signal types produce a valid taxonomy
5. Canonical step ranking stability
6. No forbidden side effects (AST safety gate)
7. TASK 039-S1 models remain immutable
"""

import ast
import inspect
import pytest

from src.services.governance.recovery.recovery_models import (
    RecoverySignal,
    RecoverySignalType,
    RecoverySeverity,
    RecoveryStepType,
    DiagnosisClassification,
)
from src.services.governance.recovery.recovery_classifier import (
    RecoveryClassifier,
    RecoveryFailureTaxonomy,
    ClassifiedDiagnosis,
    _SIGNAL_TO_TAXONOMY,
    _TAXONOMY_TO_CLASSIFICATION,
    _TAXONOMY_CONFIDENCE,
    _TAXONOMY_HYPOTHESIS,
)
from src.services.governance.recovery.recovery_plan_builder import (
    RecoveryPlanBuilder,
    _TAXONOMY_TO_STEPS,
    _STEP_REASON,
    _STEP_DURATION_SECONDS,
)
from src.services.governance.recovery.recovery_safety import (
    check_recovery_code_safety,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_signal(
    signal_type: str,
    severity: str = RecoverySeverity.HIGH.value,
    source: str = "test_monitor",
    epoch: int = 1,
    seq_id: int = 0,
    evidence_hashes=("abc123",),
    metadata=None,
) -> RecoverySignal:
    return RecoverySignal(
        source=source,
        signal_type=signal_type,
        severity=severity,
        epoch=epoch,
        seq_id=seq_id,
        evidence_hashes=tuple(evidence_hashes),
        metadata=metadata or {},
    )


CLASSIFIER = RecoveryClassifier()
BUILDER = RecoveryPlanBuilder()


# ---------------------------------------------------------------------------
# 1. Classifier determinism
# ---------------------------------------------------------------------------

class TestClassifierDeterminism:

    @pytest.mark.parametrize("signal_type", [e.value for e in RecoverySignalType])
    def test_identical_signal_produces_identical_diagnosis(self, signal_type):
        """Identical signal → identical ClassifiedDiagnosis (determinism)."""
        sig = make_signal(signal_type)
        result_a = CLASSIFIER.classify(sig)
        result_b = CLASSIFIER.classify(sig)

        assert result_a.taxonomy == result_b.taxonomy
        assert result_a.signal_hash == result_b.signal_hash
        assert result_a.diagnosis.classification == result_b.diagnosis.classification
        assert result_a.diagnosis.confidence == result_b.diagnosis.confidence
        assert result_a.diagnosis.root_cause_hypothesis == result_b.diagnosis.root_cause_hypothesis

    def test_different_signals_can_differ(self):
        """Different signal types produce different taxonomies where expected."""
        sig_health = make_signal(RecoverySignalType.HEALTH_CHECK_FAILURE.value)
        sig_quorum = make_signal(RecoverySignalType.QUORUM_LOSS.value)

        r_health = CLASSIFIER.classify(sig_health)
        r_quorum = CLASSIFIER.classify(sig_quorum)

        assert r_health.taxonomy == RecoveryFailureTaxonomy.NODE_UNHEALTHY
        assert r_quorum.taxonomy == RecoveryFailureTaxonomy.QUORUM_DEGRADED
        assert r_health.taxonomy != r_quorum.taxonomy

    def test_signal_hash_excludes_metadata_order(self):
        """Signal hash must be stable regardless of metadata insertion order."""
        sig_a = make_signal(
            RecoverySignalType.WORKER_CRASH.value,
            metadata={"a": 1, "b": 2},
        )
        sig_b = make_signal(
            RecoverySignalType.WORKER_CRASH.value,
            metadata={"b": 2, "a": 1},
        )
        r_a = CLASSIFIER.classify(sig_a)
        r_b = CLASSIFIER.classify(sig_b)
        assert r_a.signal_hash == r_b.signal_hash


# ---------------------------------------------------------------------------
# 2. Taxonomy coverage
# ---------------------------------------------------------------------------

class TestTaxonomyCoverage:

    def test_all_taxonomy_values_exist(self):
        """All 7 required taxonomy values are present."""
        required = {
            "NODE_UNHEALTHY",
            "QUORUM_DEGRADED",
            "REPLAY_DIVERGENCE",
            "CACHE_DESYNC",
            "POLICY_GRAPH_CORRUPTION",
            "SIMULATION_WARNING_ESCALATION",
            "LEDGER_READ_FAILURE",
        }
        actual = {t.value for t in RecoveryFailureTaxonomy}
        assert required == actual

    def test_all_taxonomies_have_classification(self):
        """Every taxonomy maps to a DiagnosisClassification."""
        valid_classifications = {e.value for e in DiagnosisClassification}
        for taxonomy in RecoveryFailureTaxonomy:
            classification = _TAXONOMY_TO_CLASSIFICATION[taxonomy]
            assert classification.value in valid_classifications

    def test_all_taxonomies_have_confidence(self):
        """Every taxonomy has a deterministic confidence in [0, 1]."""
        for taxonomy in RecoveryFailureTaxonomy:
            conf = _TAXONOMY_CONFIDENCE[taxonomy]
            assert 0.0 <= conf <= 1.0, f"{taxonomy} confidence out of range: {conf}"

    def test_all_taxonomies_have_hypothesis(self):
        """Every taxonomy has a non-empty hypothesis string."""
        for taxonomy in RecoveryFailureTaxonomy:
            hyp = _TAXONOMY_HYPOTHESIS[taxonomy]
            assert isinstance(hyp, str) and len(hyp) > 0

    def test_all_taxonomies_have_plan_steps(self):
        """Every taxonomy has at least one plan step defined."""
        for taxonomy in RecoveryFailureTaxonomy:
            steps = _TAXONOMY_TO_STEPS[taxonomy]
            assert len(steps) >= 1, f"{taxonomy} has no plan steps"

    def test_all_signal_types_produce_taxonomy(self):
        """Every S1 signal type is classifiable (no KeyError / unhandled case)."""
        for signal_type in RecoverySignalType:
            sig = make_signal(signal_type.value)
            result = CLASSIFIER.classify(sig)
            assert isinstance(result.taxonomy, RecoveryFailureTaxonomy)


# ---------------------------------------------------------------------------
# 3. Explicit signal → taxonomy mapping
# ---------------------------------------------------------------------------

class TestSignalTaxonomyMappings:

    @pytest.mark.parametrize("signal_type,expected_taxonomy", [
        (RecoverySignalType.HEALTH_CHECK_FAILURE, RecoveryFailureTaxonomy.NODE_UNHEALTHY),
        (RecoverySignalType.WORKER_CRASH,         RecoveryFailureTaxonomy.NODE_UNHEALTHY),
        (RecoverySignalType.TIMEOUT_DETECTED,     RecoveryFailureTaxonomy.NODE_UNHEALTHY),
        (RecoverySignalType.QUORUM_LOSS,          RecoveryFailureTaxonomy.QUORUM_DEGRADED),
        (RecoverySignalType.LEDGER_DIVERGENCE,    RecoveryFailureTaxonomy.REPLAY_DIVERGENCE),
        (RecoverySignalType.SQLITE_CORRUPTION,    RecoveryFailureTaxonomy.CACHE_DESYNC),
        (RecoverySignalType.REPLICATION_LAG,      RecoveryFailureTaxonomy.CACHE_DESYNC),
        (RecoverySignalType.POLICY_VIOLATION,     RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION),
    ])
    def test_signal_type_maps_to_expected_taxonomy(self, signal_type, expected_taxonomy):
        sig = make_signal(signal_type.value)
        result = CLASSIFIER.classify(sig)
        assert result.taxonomy == expected_taxonomy

    def test_simulation_escalation_metadata_override(self):
        """simulation_escalation=True metadata overrides to SIMULATION_WARNING_ESCALATION."""
        sig = make_signal(
            RecoverySignalType.POLICY_VIOLATION.value,
            metadata={"simulation_escalation": True},
        )
        result = CLASSIFIER.classify(sig)
        assert result.taxonomy == RecoveryFailureTaxonomy.SIMULATION_WARNING_ESCALATION

    def test_simulation_escalation_false_does_not_override(self):
        """simulation_escalation=False must NOT trigger SIMULATION_WARNING_ESCALATION."""
        sig = make_signal(
            RecoverySignalType.POLICY_VIOLATION.value,
            metadata={"simulation_escalation": False},
        )
        result = CLASSIFIER.classify(sig)
        assert result.taxonomy == RecoveryFailureTaxonomy.POLICY_GRAPH_CORRUPTION


# ---------------------------------------------------------------------------
# 4. Plan builder determinism
# ---------------------------------------------------------------------------

class TestPlanBuilderDeterminism:

    @pytest.mark.parametrize("signal_type", [e.value for e in RecoverySignalType])
    def test_identical_diagnosis_produces_identical_plan(self, signal_type):
        """Identical ClassifiedDiagnosis → identical RecoveryPlan."""
        sig = make_signal(signal_type)
        classified = CLASSIFIER.classify(sig)

        plan_a = BUILDER.build(classified, target="node_1")
        plan_b = BUILDER.build(classified, target="node_1")

        assert plan_a.steps == plan_b.steps
        assert plan_a.estimated_duration_seconds == plan_b.estimated_duration_seconds
        assert plan_a.rollback_plan_hash == plan_b.rollback_plan_hash

    def test_different_targets_differ_in_rollback_hash(self):
        """Different target strings produce different rollback hashes."""
        sig = make_signal(RecoverySignalType.WORKER_CRASH.value)
        classified = CLASSIFIER.classify(sig)

        plan_a = BUILDER.build(classified, target="node_1")
        plan_b = BUILDER.build(classified, target="node_2")

        assert plan_a.rollback_plan_hash != plan_b.rollback_plan_hash


# ---------------------------------------------------------------------------
# 5. Explicit taxonomy → steps mappings per task spec
# ---------------------------------------------------------------------------

class TestExplicitStepMappings:

    def _step_types(self, plan) -> tuple:
        return tuple(s.step_type for s in plan.steps)

    def _classify_and_build(self, signal_type_value, metadata=None, target="system"):
        sig = make_signal(signal_type_value, metadata=metadata)
        classified = CLASSIFIER.classify(sig)
        plan = BUILDER.build(classified, target=target)
        return plan

    def test_node_unhealthy_steps(self):
        plan = self._classify_and_build(RecoverySignalType.HEALTH_CHECK_FAILURE.value)
        step_types = self._step_types(plan)
        assert RecoveryStepType.ISOLATE_WORKER.value in step_types
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types
        assert RecoveryStepType.RESTART_NODE.value in step_types

    def test_cache_desync_steps(self):
        plan = self._classify_and_build(RecoverySignalType.SQLITE_CORRUPTION.value)
        step_types = self._step_types(plan)
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types
        assert RecoveryStepType.REBUILD_SQLITE_PROJECTION.value in step_types

    def test_replay_divergence_steps(self):
        plan = self._classify_and_build(RecoverySignalType.LEDGER_DIVERGENCE.value)
        step_types = self._step_types(plan)
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types
        assert RecoveryStepType.ROLLBACK_TO_LEDGER_POINT.value in step_types

    def test_quorum_degraded_steps(self):
        plan = self._classify_and_build(RecoverySignalType.QUORUM_LOSS.value)
        step_types = self._step_types(plan)
        assert RecoveryStepType.REQUEST_QUORUM_REPAIR.value in step_types

    def test_policy_graph_corruption_steps(self):
        plan = self._classify_and_build(RecoverySignalType.POLICY_VIOLATION.value)
        step_types = self._step_types(plan)
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types
        assert RecoveryStepType.ROLLBACK_TO_LEDGER_POINT.value in step_types

    def test_ledger_read_failure_steps(self):
        # Trigger via unknown signal type fallback is not possible via S1 signal,
        # but we can trigger via simulation_escalation=False + REPLICATION_LAG
        # For direct test: use a classified signal with LEDGER_READ_FAILURE taxonomy
        sig = make_signal(RecoverySignalType.REPLICATION_LAG.value)
        classified = CLASSIFIER.classify(sig)
        # Manually build with forced taxonomy via a fresh classified
        sig2 = make_signal(RecoverySignalType.LEDGER_DIVERGENCE.value)
        c2 = CLASSIFIER.classify(sig2)
        # LEDGER_READ_FAILURE taxonomy is reachable as fail-safe; test builder directly
        from src.services.governance.recovery.recovery_classifier import (
            ClassifiedDiagnosis,
            RecoveryFailureTaxonomy,
            _TAXONOMY_TO_CLASSIFICATION,
            _TAXONOMY_CONFIDENCE,
            _TAXONOMY_HYPOTHESIS,
        )
        from src.services.governance.recovery.recovery_models import RecoveryDiagnosis
        from src.services.governance.recovery.recovery_report_hasher import compute_signal_hash

        taxonomy = RecoveryFailureTaxonomy.LEDGER_READ_FAILURE
        diagnosis = RecoveryDiagnosis(
            classification=_TAXONOMY_TO_CLASSIFICATION[taxonomy].value,
            identified_failures=(taxonomy.value, f"signal:{sig2.signal_type}"),
            root_cause_hypothesis=_TAXONOMY_HYPOTHESIS[taxonomy],
            confidence=_TAXONOMY_CONFIDENCE[taxonomy],
            evidence_count=1,
        )
        classified_lr = ClassifiedDiagnosis(
            taxonomy=taxonomy,
            diagnosis=diagnosis,
            signal_hash=compute_signal_hash(sig2),
        )
        plan = BUILDER.build(classified_lr, target="ledger")
        step_types = self._step_types(plan)
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types

    def test_simulation_warning_escalation_steps(self):
        sig = make_signal(
            RecoverySignalType.POLICY_VIOLATION.value,
            metadata={"simulation_escalation": True},
        )
        classified = CLASSIFIER.classify(sig)
        plan = BUILDER.build(classified, target="simulation")
        step_types = self._step_types(plan)
        assert RecoveryStepType.RUN_REPLAY_VERIFICATION.value in step_types


# ---------------------------------------------------------------------------
# 6. Canonical ranking stability
# ---------------------------------------------------------------------------

class TestCanonicalRankingStability:

    def test_step_order_is_stable_across_calls(self):
        """Step ordering must be identical across repeated plan builds."""
        sig = make_signal(RecoverySignalType.HEALTH_CHECK_FAILURE.value)
        classified = CLASSIFIER.classify(sig)

        plans = [BUILDER.build(classified, target="worker_x") for _ in range(5)]
        first_order = [s.step_type for s in plans[0].steps]

        for plan in plans[1:]:
            assert [s.step_type for s in plan.steps] == first_order

    def test_plan_is_frozen(self):
        """RecoveryPlan must be frozen (immutable)."""
        sig = make_signal(RecoverySignalType.WORKER_CRASH.value)
        classified = CLASSIFIER.classify(sig)
        plan = BUILDER.build(classified)

        assert getattr(plan.__class__, "__dataclass_params__").frozen

    def test_classified_diagnosis_is_frozen(self):
        """ClassifiedDiagnosis must be frozen."""
        sig = make_signal(RecoverySignalType.SQLITE_CORRUPTION.value)
        classified = CLASSIFIER.classify(sig)

        assert getattr(classified.__class__, "__dataclass_params__").frozen

    def test_rollback_hash_is_stable(self):
        """Rollback hash must be identical for same taxonomy + target."""
        sig = make_signal(RecoverySignalType.QUORUM_LOSS.value)
        classified = CLASSIFIER.classify(sig)

        hashes = [BUILDER.build(classified, target="mesh").rollback_plan_hash for _ in range(3)]
        assert len(set(hashes)) == 1


# ---------------------------------------------------------------------------
# 7. No forbidden side effects (AST safety gate)
# ---------------------------------------------------------------------------

class TestNoForbiddenSideEffects:

    def _get_source(self, module) -> str:
        return inspect.getsource(module)

    def test_classifier_has_no_forbidden_calls(self):
        import src.services.governance.recovery.recovery_classifier as mod
        source = self._get_source(mod)
        is_safe, violations = check_recovery_code_safety(source)
        assert is_safe, f"Classifier safety violations:\n" + "\n".join(violations)

    def test_plan_builder_has_no_forbidden_calls(self):
        import src.services.governance.recovery.recovery_plan_builder as mod
        source = self._get_source(mod)
        is_safe, violations = check_recovery_code_safety(source)
        assert is_safe, f"Plan builder safety violations:\n" + "\n".join(violations)

    def test_classifier_has_no_mesh_imports(self):
        import ast as _ast
        import src.services.governance.recovery.recovery_classifier as mod
        source = self._get_source(mod)
        assert "MeshOrchestrator" not in source
        # Check import statements only (not docstrings/comments)
        tree = _ast.parse(source)
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    assert "mesh" not in alias.name.lower(), \
                        f"Forbidden mesh import: {alias.name}"
            elif isinstance(node, _ast.ImportFrom):
                module = node.module or ""
                assert "mesh" not in module.lower(), \
                    f"Forbidden mesh module import: {module}"


    def test_plan_builder_has_no_mesh_imports(self):
        import src.services.governance.recovery.recovery_plan_builder as mod
        source = self._get_source(mod)
        assert "MeshOrchestrator" not in source

    def test_classifier_has_no_ledger_writes(self):
        import src.services.governance.recovery.recovery_classifier as mod
        source = self._get_source(mod)
        forbidden = ["append_event", "commit_event", "write_ledger", "submit_event"]
        for sym in forbidden:
            assert sym not in source, f"Classifier contains forbidden symbol: {sym}"

    def test_plan_builder_has_no_ledger_writes(self):
        import src.services.governance.recovery.recovery_plan_builder as mod
        source = self._get_source(mod)
        forbidden = ["append_event", "commit_event", "write_ledger", "promote"]
        for sym in forbidden:
            assert sym not in source, f"Plan builder contains forbidden symbol: {sym}"


# ---------------------------------------------------------------------------
# 8. S1 invariants still hold
# ---------------------------------------------------------------------------

class TestS1InvariantsStillHold:

    def test_s1_models_still_frozen(self):
        """S1 core models remain frozen/immutable."""
        from src.services.governance.recovery.recovery_models import (
            RecoverySignal, RecoveryDiagnosis, RecoveryStep,
            RecoveryPlan, RecoveryProposal, RecoveryReport,
        )
        for cls in [RecoverySignal, RecoveryDiagnosis, RecoveryStep,
                    RecoveryPlan, RecoveryProposal, RecoveryReport]:
            assert getattr(cls, "__dataclass_params__").frozen, f"{cls.__name__} is not frozen"

    def test_s1_signal_validation_still_enforced(self):
        """S1 signal validation rejects invalid signal types."""
        with pytest.raises(ValueError):
            RecoverySignal(
                source="test",
                signal_type="INVALID_TYPE",
                severity=RecoverySeverity.HIGH.value,
                epoch=1,
                seq_id=0,
                evidence_hashes=("h1",),
            )

    def test_s1_evidence_hashes_still_sorted(self):
        """S1 evidence hash sorting is deterministic."""
        sig = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.WORKER_CRASH.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("zzz", "aaa", "mmm"),
        )
        assert sig.evidence_hashes == ("aaa", "mmm", "zzz")

    def test_s2_classifier_does_not_modify_input_signal(self):
        """Classifier must not mutate the input signal."""
        sig = make_signal(RecoverySignalType.HEALTH_CHECK_FAILURE.value)
        original_hash = id(sig)
        original_evidence = sig.evidence_hashes

        _ = CLASSIFIER.classify(sig)

        assert id(sig) == original_hash
        assert sig.evidence_hashes == original_evidence

    def test_s2_plan_builder_does_not_modify_classified_input(self):
        """Plan builder must not mutate the ClassifiedDiagnosis input."""
        sig = make_signal(RecoverySignalType.WORKER_CRASH.value)
        classified = CLASSIFIER.classify(sig)
        original_taxonomy = classified.taxonomy
        original_hash = classified.signal_hash

        _ = BUILDER.build(classified)

        assert classified.taxonomy == original_taxonomy
        assert classified.signal_hash == original_hash
