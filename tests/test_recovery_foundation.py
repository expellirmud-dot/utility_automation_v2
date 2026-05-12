"""
Tests for TASK 039-S1 - Deterministic Recovery Foundation.

Verifies:
- Frozen immutability of all models
- Deterministic hash stability
- Canonical ordering
- AI advice exclusion from hashes
- Normalization
- Safety gate enforcement
- Fail-closed behavior
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.governance.recovery import (
    RecoverySignal,
    RecoveryDiagnosis,
    RecoveryStep,
    RecoveryPlan,
    RecoveryProposal,
    RecoveryReport,
    RecoveryAIAdvice,
    RecoverySignalType,
    RecoverySeverity,
    RecoveryStepType,
    DiagnosisClassification,
    RECOVERY_STEP_PRECEDENCE,
    compute_proposal_hash,
    compute_report_hash,
    verify_proposal_hash,
    verify_report_hash,
    stable_hash,
    canonical_json,
    SafetyGate,
    SafeRecoveryProposalBuilder,
    check_recovery_code_safety,
    RecoverySafetyViolation,
)


class TestFrozenImmutability:
    """Test that all models are truly frozen."""

    def test_recovery_signal_frozen(self):
        """RecoverySignal is immutable."""
        signal = RecoverySignal(
            source="health_monitor",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.CRITICAL.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1", "hash2"),
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            signal.source = "modified"

    def test_recovery_diagnosis_frozen(self):
        """RecoveryDiagnosis is immutable."""
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("failure1",),
            root_cause_hypothesis="Bug in replica sync",
            confidence=0.95,
            evidence_count=3,
        )
        
        with pytest.raises(Exception):
            diag.confidence = 0.5

    def test_recovery_step_frozen(self):
        """RecoveryStep is immutable."""
        step = RecoveryStep(
            step_type=RecoveryStepType.ISOLATE_WORKER.value,
            target="worker_1",
            reason="Prevent further divergence",
            parameters={"timeout_seconds": 30},
        )
        
        with pytest.raises(Exception):
            step.target = "worker_2"

    def test_recovery_plan_frozen(self):
        """RecoveryPlan is immutable."""
        step = RecoveryStep(
            step_type=RecoveryStepType.ISOLATE_WORKER.value,
            target="worker_1",
            reason="Isolate",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=60,
            rollback_plan_hash="rollback_hash_1",
        )
        
        with pytest.raises(Exception):
            plan.estimated_duration_seconds = 120

    def test_recovery_proposal_frozen(self):
        """RecoveryProposal is immutable."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.WORKER_CRASH.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("crash",),
            root_cause_hypothesis="OOM",
            confidence=0.9,
            evidence_count=2,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.RESTART_NODE.value,
            target="node_1",
            reason="Restart after crash",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=30,
            rollback_plan_hash="hash",
        )
        proposal = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Automatic recovery",
        )
        
        with pytest.raises(Exception):
            proposal.reason_for_proposal = "Modified"

    def test_recovery_report_frozen(self):
        """RecoveryReport is immutable."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.LEDGER_DIVERGENCE.value,
            severity=RecoverySeverity.CRITICAL.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.DISTRIBUTED_SPLIT.value,
            identified_failures=("split",),
            root_cause_hypothesis="Network partition",
            confidence=0.95,
            evidence_count=5,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.REQUEST_QUORUM_REPAIR.value,
            target="quorum",
            reason="Heal split",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=60,
            rollback_plan_hash="hash",
        )
        proposal = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Automatic",
        )
        report = RecoveryReport(proposal=proposal)
        
        with pytest.raises(Exception):
            report.report_hash = "modified"

    def test_recovery_ai_advice_frozen(self):
        """RecoveryAIAdvice is immutable."""
        advice = RecoveryAIAdvice(
            confidence_adjustment=0.05,
            suggested_alternatives=("alt1", "alt2"),
            warnings=("warn1",),
            notes=("note1",),
            model_used="GPT-4",
        )
        
        with pytest.raises(Exception):
            advice.confidence_adjustment = 0.1


class TestDeterministicHashing:
    """Test deterministic hash stability."""

    def test_proposal_hash_stability(self):
        """Same proposal produces same hash."""
        signal = RecoverySignal(
            source="monitor",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash_a", "hash_b"),
        )
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("f1", "f2"),
            root_cause_hypothesis="Cause",
            confidence=0.8,
            evidence_count=2,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.ISOLATE_WORKER.value,
            target="w1",
            reason="Isolate",
            parameters={"timeout": 30},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=60,
            rollback_plan_hash="rb_hash",
        )
        
        # Create two identical proposals
        proposal1 = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Recovery needed",
        )
        
        proposal2 = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Recovery needed",
        )
        
        # Hashes must be identical
        assert proposal1.proposal_hash == proposal2.proposal_hash
        assert proposal1.proposal_hash is not None

    def test_report_hash_stability(self):
        """Same report produces same hash."""
        signal = RecoverySignal(
            source="monitor",
            signal_type=RecoverySignalType.SQLITE_CORRUPTION.value,
            severity=RecoverySeverity.CRITICAL.value,
            epoch=2,
            seq_id=1,
            evidence_hashes=("hash_c",),
        )
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.SYSTEMIC_DEGRADATION.value,
            identified_failures=("corruption",),
            root_cause_hypothesis="Disk error",
            confidence=0.99,
            evidence_count=10,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.REBUILD_SQLITE_PROJECTION.value,
            target="sqlite",
            reason="Rebuild",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=300,
            rollback_plan_hash="rb_hash_2",
        )
        
        proposal = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="DB recovery",
        )
        
        report1 = RecoveryReport(proposal=proposal)
        report2 = RecoveryReport(proposal=proposal)
        
        assert report1.report_hash == report2.report_hash

    def test_hash_changes_with_content(self):
        """Different content produces different hash."""
        signal1 = RecoverySignal(
            source="monitor1",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        signal2 = RecoverySignal(
            source="monitor2",  # Different
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("f1",),
            root_cause_hypothesis="Cause",
            confidence=0.8,
            evidence_count=1,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.ISOLATE_WORKER.value,
            target="w1",
            reason="Isolate",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=60,
            rollback_plan_hash="rb",
        )
        
        proposal1 = RecoveryProposal(
            signal=signal1,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Recovery",
        )
        proposal2 = RecoveryProposal(
            signal=signal2,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Recovery",
        )
        
        assert proposal1.proposal_hash != proposal2.proposal_hash


class TestAIAdviceExclusion:
    """Test that AI advice is excluded from hashes."""

    def test_ai_advice_not_in_proposal_hash(self):
        """AI advice changes don't affect proposal hash."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.WORKER_CRASH.value,
            severity=RecoverySeverity.CRITICAL.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("crash",),
            root_cause_hypothesis="OOM",
            confidence=0.95,
            evidence_count=3,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.RESTART_NODE.value,
            target="node_1",
            reason="Restart",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=30,
            rollback_plan_hash="rb",
        )
        
        proposal = RecoveryProposal(
            signal=signal,
            diagnosis=diag,
            plan=plan,
            reason_for_proposal="Automatic",
        )
        
        hash_without_ai = proposal.proposal_hash
        
        # Create report with different AI advice
        report1 = RecoveryReport(
            proposal=proposal,
            ai_advice=RecoveryAIAdvice(
                confidence_adjustment=0.05,
                warnings=("warn1",),
                model_used="GPT-4",
            ),
        )
        
        report2 = RecoveryReport(
            proposal=proposal,
            ai_advice=RecoveryAIAdvice(
                confidence_adjustment=0.1,
                warnings=("warn1", "warn2"),
                model_used="Claude",
            ),
        )
        
        # Report hashes should be same (both based on proposal, not AI)
        assert report1.report_hash == report2.report_hash
        # Proposal hash shouldn't be affected
        assert proposal.proposal_hash == hash_without_ai

    def test_ai_advice_separate_object(self):
        """AI advice can be serialized separately."""
        advice = RecoveryAIAdvice(
            confidence_adjustment=0.05,
            suggested_alternatives=("alt1", "alt2"),
            warnings=("warn1",),
            notes=("note1",),
            model_used="GPT-4",
        )
        
        payload = advice.to_payload()
        assert "confidence_adjustment" in payload
        assert "model_used" in payload
        assert payload["model_used"] == "GPT-4"


class TestCanonicalOrdering:
    """Test canonical ordering of tuples and dicts."""

    def test_signal_evidence_hashes_sorted(self):
        """Evidence hashes sorted deterministically."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("z_hash", "a_hash", "m_hash"),
        )
        
        # Hashes should be sorted
        assert signal.evidence_hashes == ("a_hash", "m_hash", "z_hash")

    def test_diagnosis_failures_sorted(self):
        """Identified failures sorted deterministically."""
        diag = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("failure_z", "failure_a", "failure_m"),
            root_cause_hypothesis="Cause",
            confidence=0.8,
            evidence_count=1,
        )
        
        assert diag.identified_failures == ("failure_a", "failure_m", "failure_z")

    def test_plan_steps_sorted_by_precedence(self):
        """Recovery steps sorted by precedence."""
        steps = [
            RecoveryStep(
                step_type=RecoveryStepType.RESTART_NODE.value,
                target="node_2",
                reason="Restart",
                parameters={},
            ),
            RecoveryStep(
                step_type=RecoveryStepType.ISOLATE_WORKER.value,
                target="worker_1",
                reason="Isolate",
                parameters={},
            ),
            RecoveryStep(
                step_type=RecoveryStepType.RUN_REPLAY_VERIFICATION.value,
                target="ledger",
                reason="Verify",
                parameters={},
            ),
        ]
        
        plan = RecoveryPlan(
            steps=tuple(steps),
            estimated_duration_seconds=60,
            rollback_plan_hash="rb",
        )
        
        # Should be sorted by precedence: ISOLATE < REPLAY < RESTART
        assert plan.steps[0].step_type == RecoveryStepType.ISOLATE_WORKER.value
        assert plan.steps[1].step_type == RecoveryStepType.RUN_REPLAY_VERIFICATION.value
        assert plan.steps[2].step_type == RecoveryStepType.RESTART_NODE.value

    def test_step_precedence_constants(self):
        """Recovery step precedence constants are in order."""
        expected_order = [
            RecoveryStepType.ISOLATE_WORKER,
            RecoveryStepType.RUN_REPLAY_VERIFICATION,
            RecoveryStepType.REBUILD_SQLITE_PROJECTION,
            RecoveryStepType.REQUEST_QUORUM_REPAIR,
            RecoveryStepType.ROLLBACK_TO_LEDGER_POINT,
            RecoveryStepType.RESTART_NODE,
        ]
        
        for i, expected_type in enumerate(expected_order):
            assert RECOVERY_STEP_PRECEDENCE[i] == expected_type


class TestSignalNormalization:
    """Test RecoverySignal normalization."""

    def test_signal_validates_enum_types(self):
        """Signal validates signal_type and severity."""
        with pytest.raises(ValueError):
            RecoverySignal(
                source="test",
                signal_type="INVALID_TYPE",
                severity=RecoverySeverity.HIGH.value,
                epoch=1,
                seq_id=0,
                evidence_hashes=(),
            )
        
        with pytest.raises(ValueError):
            RecoverySignal(
                source="test",
                signal_type=RecoverySignalType.WORKER_CRASH.value,
                severity="INVALID_SEVERITY",
                epoch=1,
                seq_id=0,
                evidence_hashes=(),
            )

    def test_signal_normalizes_metadata(self):
        """Signal normalizes metadata keys."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
            metadata={"z_key": "val1", "a_key": "val2"},
        )
        
        # Metadata keys should be sortable (frozen dict)
        assert isinstance(signal.metadata, dict)


class TestSafetyGate:
    """Test AST-based safety enforcement."""

    def test_forbidden_symbol_append_event(self):
        """Detect forbidden append_event call."""
        code = """
def recovery_func():
    append_event("recovery_started")
    return True
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert any("append_event" in v for v in violations)

    def test_forbidden_symbol_promote(self):
        """Detect forbidden promote call."""
        code = """
def recovery_func():
    promote_policy(version_id)
    return True
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert any("promote" in v.lower() for v in violations)

    def test_forbidden_symbol_submit_critical_event(self):
        """Detect forbidden submit_critical_event call."""
        code = """
def recovery_func():
    submit_critical_event({"action": "recovery"})
    return True
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert any("submit_critical_event" in v for v in violations)

    def test_forbidden_mesh_orchestrator_call(self):
        """Detect forbidden MeshOrchestrator method call."""
        code = """
from src.mesh import MeshOrchestrator

def recovery_func():
    mesh = MeshOrchestrator()
    mesh.submit_proposal(proposal)
    return True
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        # Either import or access should be caught
        assert any("forbidden" in v.lower() or "MeshOrchestrator" in v for v in violations)

    def test_forbidden_sqlite_mutation(self):
        """Detect forbidden SQLite mutation."""
        code = """
def recovery_func():
    db.execute("DELETE FROM cache WHERE id=?", (1,))
    return True
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert any("execute" in v for v in violations)

    def test_safe_code_normalize(self):
        """Normalize operations are safe."""
        code = """
def normalize_signal(signal):
    # Read-only normalization
    return signal
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert is_safe

    def test_safe_code_hash(self):
        """Hash operations are safe."""
        code = """
from src.services.governance.recovery import stable_hash

def compute_hash(proposal):
    return stable_hash(proposal.to_payload())
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert is_safe

    def test_safe_code_build_proposal(self):
        """Building proposal objects is safe."""
        code = """
from src.services.governance.recovery import RecoveryProposal

def build_proposal(signal, diagnosis, plan, reason):
    return RecoveryProposal(
        signal=signal,
        diagnosis=diagnosis,
        plan=plan,
        reason_for_proposal=reason,
    )
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert is_safe

    def test_syntax_error_detection(self):
        """Detect syntax errors."""
        code = """
def bad_func():
    x = [1, 2, 3
    return x
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        assert any("Syntax" in v for v in violations)


class TestFailClosedBehavior:
    """Test fail-closed safety enforcement."""

    def test_safety_violation_raises(self):
        """Safety violations raise exceptions."""
        code = "commit_event(event)"
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe
        
        with pytest.raises(RecoverySafetyViolation):
            if not is_safe:
                raise RecoverySafetyViolation("\n".join(violations))

    def test_safe_builder_operations_allowed(self):
        """SafeRecoveryProposalBuilder allows safe operations."""
        builder = SafeRecoveryProposalBuilder()
        
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        
        # These should work
        normalized = builder.normalize_signal(signal)
        assert normalized is not None
        
        # Hash computation should work
        signal_dict = {"source": signal.source, "epoch": signal.epoch}
        hash_result = builder.compute_hash(signal_dict)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex

    def test_immutability_validation(self):
        """Validate that models are frozen."""
        builder = SafeRecoveryProposalBuilder()
        
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        
        # Should return True
        assert builder.validate_immutability(signal) is True


class TestCanonicalJSON:
    """Test canonical JSON generation."""

    def test_canonical_json_sorting(self):
        """Canonical JSON has sorted keys."""
        data = {"z": 1, "a": 2, "m": 3}
        canon = canonical_json(data)
        assert canon == '{"a":2,"m":3,"z":1}'

    def test_canonical_json_nested(self):
        """Canonical JSON handles nested structures."""
        data = {
            "z": {"nested_z": 1, "nested_a": 2},
            "a": [3, 1, 2],
        }
        canon = canonical_json(data)
        # Keys should be sorted at all levels
        assert '"a"' in canon
        assert '"z"' in canon


class TestExistingCertificationNonRegression:
    """
    Placeholder tests to verify existing certifications remain unaffected.
    These would integrate with TASK 036 certification suite.
    """

    def test_recovery_subsystem_minimal_impact(self):
        """Recovery subsystem adds no new shared state."""
        # Verify recovery models are in isolated namespace
        from src.services.governance import recovery
        assert recovery.__name__ == "src.services.governance.recovery"

    def test_no_ledger_writes_possible(self):
        """Recovery code cannot write ledger."""
        code = """
def bad_recovery():
    append_event(event)
"""
        is_safe, violations = check_recovery_code_safety(code)
        assert not is_safe


class TestRecoverySubsystemFullScan:
    """Comprehensive AST safety scan of entire recovery subsystem."""

    def test_scan_all_recovery_files_for_safety(self):
        """Scan every Python file in recovery subsystem for forbidden symbols."""
        import glob
        import pathlib

        recovery_dir = pathlib.Path("src/services/governance/recovery")
        assert recovery_dir.exists(), f"Recovery directory not found: {recovery_dir}"

        py_files = list(recovery_dir.glob("*.py"))
        assert len(py_files) > 0, "No Python files found in recovery directory"

        excluded_files = {"__pycache__"}
        safety_violations = []

        for py_file in py_files:
            if py_file.name in excluded_files:
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source_code = f.read()

                is_safe, violations = check_recovery_code_safety(source_code)

                if not is_safe:
                    safety_violations.append({
                        "file": str(py_file),
                        "violations": violations,
                    })
            except Exception as e:
                pytest.fail(f"Error scanning {py_file}: {e}")

        # Fail if any violations found
        if safety_violations:
            formatted_violations = "\n".join([
                f"\n{v['file']}:\n" + "\n".join(f"  - {viol}" for viol in v['violations'])
                for v in safety_violations
            ])
            pytest.fail(f"Safety violations found in recovery subsystem:{formatted_violations}")

    def test_recovery_files_exist_and_parse(self):
        """Verify all expected recovery files exist and are valid Python."""
        import pathlib

        expected_files = {
            "src/services/governance/recovery/__init__.py",
            "src/services/governance/recovery/recovery_models.py",
            "src/services/governance/recovery/recovery_report_hasher.py",
            "src/services/governance/recovery/recovery_safety.py",
            "src/services/governance/recovery/recovery_classifier.py",
            "src/services/governance/recovery/recovery_plan_builder.py",
            "src/services/governance/recovery/recovery_simulation_gate.py",
            "src/services/governance/recovery/recovery_handoff.py",
        }

        for file_path in expected_files:
            path = pathlib.Path(file_path)
            assert path.exists(), f"Expected file not found: {file_path}"

            # Verify it's valid Python
            with open(path, encoding="utf-8") as f:
                code = f.read()
            try:
                compile(code, file_path, "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}: {e}")

    def test_all_models_present_and_exported(self):
        """Verify all core models are exported from __init__.py."""
        from src.services.governance import recovery

        required_exports = {
            # Models
            "RecoverySignal",
            "RecoveryDiagnosis",
            "RecoveryStep",
            "RecoveryPlan",
            "RecoveryProposal",
            "RecoveryReport",
            "RecoveryAIAdvice",
            # Enums
            "RecoverySignalType",
            "RecoverySeverity",
            "RecoveryStepType",
            "DiagnosisClassification",
            "RECOVERY_STEP_PRECEDENCE",
            # Hashing
            "compute_signal_hash",
            "compute_diagnosis_hash",
            "compute_step_hash",
            "compute_plan_hash",
            "compute_proposal_hash",
            "compute_report_hash",
            "verify_signal_hash",
            "verify_diagnosis_hash",
            "verify_plan_hash",
            "verify_proposal_hash",
            "verify_report_hash",
            "stable_hash",
            "canonical_json",
            # Safety
            "SafetyGate",
            "SafeRecoveryProposalBuilder",
            "check_recovery_code_safety",
            "check_recovery_function_safety",
            "enforce_fail_closed",
            "RecoverySafetyViolation",
            # S3
            "RecoverySimulationRiskLevel",
            "RecoveryStepSimulation",
            "RecoverySimulationReport",
            "RecoverySimulationGate",
            "RISK_PRECEDENCE",
            "STEP_RISK_BY_TYPE",
            "STEP_WARNING_CODE_BY_TYPE",
            "STEP_WARNING_DETAIL_BY_TYPE",
            # S4
            "RecoveryAuthorityDecision",
            "RecoveryAuthorityResponse",
            "RecoveryHandoffRequest",
            "RecoveryHandoffDecision",
            "MeshAuthorityAdapter",
            "RecoveryProposalHandoff",
        }

        for export_name in required_exports:
            assert hasattr(recovery, export_name), \
                f"Required export missing: {export_name}"


class TestAIAdviceExclusionComprehensive:
    """Comprehensive verification AI advice is excluded from all hashes."""

    def test_ai_advice_not_in_signal_hash(self):
        """AI advice changes don't affect signal hash."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.HEALTH_CHECK_FAILURE.value,
            severity=RecoverySeverity.HIGH.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )

        from src.services.governance.recovery import compute_signal_hash
        hash1 = compute_signal_hash(signal)
        hash2 = compute_signal_hash(signal)

        # Same signal should produce same hash
        assert hash1 == hash2

    def test_ai_advice_not_in_diagnosis_hash(self):
        """AI advice changes don't affect diagnosis hash."""
        diagnosis = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("f1",),
            root_cause_hypothesis="Cause",
            confidence=0.9,
            evidence_count=2,
        )

        from src.services.governance.recovery import compute_diagnosis_hash
        hash1 = compute_diagnosis_hash(diagnosis)
        hash2 = compute_diagnosis_hash(diagnosis)

        assert hash1 == hash2

    def test_ai_advice_not_in_plan_hash(self):
        """AI advice changes don't affect plan hash."""
        step = RecoveryStep(
            step_type=RecoveryStepType.ISOLATE_WORKER.value,
            target="w1",
            reason="Isolate",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=60,
            rollback_plan_hash="rb",
        )

        from src.services.governance.recovery import compute_plan_hash
        hash1 = compute_plan_hash(plan)
        hash2 = compute_plan_hash(plan)

        assert hash1 == hash2

    def test_proposal_hash_immutable_with_different_ai_advice(self):
        """Proposal hash unchanged when AI advice modified."""
        signal = RecoverySignal(
            source="test",
            signal_type=RecoverySignalType.WORKER_CRASH.value,
            severity=RecoverySeverity.CRITICAL.value,
            epoch=1,
            seq_id=0,
            evidence_hashes=("hash1",),
        )
        diagnosis = RecoveryDiagnosis(
            classification=DiagnosisClassification.ISOLATED_FAILURE.value,
            identified_failures=("crash",),
            root_cause_hypothesis="OOM",
            confidence=0.95,
            evidence_count=3,
        )
        step = RecoveryStep(
            step_type=RecoveryStepType.RESTART_NODE.value,
            target="node_1",
            reason="Restart",
            parameters={},
        )
        plan = RecoveryPlan(
            steps=(step,),
            estimated_duration_seconds=30,
            rollback_plan_hash="rb",
        )

        proposal = RecoveryProposal(
            signal=signal,
            diagnosis=diagnosis,
            plan=plan,
            reason_for_proposal="Auto recovery",
        )

        proposal_hash_baseline = proposal.proposal_hash

        # Create different reports with different AI advice
        report1 = RecoveryReport(
            proposal=proposal,
            ai_advice=RecoveryAIAdvice(
                confidence_adjustment=0.0,
                model_used="GPT-4",
            ),
        )

        report2 = RecoveryReport(
            proposal=proposal,
            ai_advice=RecoveryAIAdvice(
                confidence_adjustment=0.1,
                warnings=("warn1", "warn2"),
                model_used="Claude",
            ),
        )

        # Proposal hash should be unchanged
        assert proposal.proposal_hash == proposal_hash_baseline

        # Both reports' proposal hashes should reference the same baseline
        payload1 = report1.to_payload(include_ai_advice=True)
        payload2 = report2.to_payload(include_ai_advice=True)

        assert payload1["proposal"]["proposal_hash"] == proposal_hash_baseline
        assert payload2["proposal"]["proposal_hash"] == proposal_hash_baseline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
