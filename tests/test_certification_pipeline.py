from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from src.tests.certification.certification_checks import registered_checks
from src.services.governance.certification.models import (
    CertificationArtifact,
    CertificationCheck,
    CertificationResult,
)
from src.tests.certification.certification_runner import CertificationRunner


def test_certification_models_are_frozen() -> None:
    check = CertificationCheck("sample", "unit", "sample check", 1)
    with pytest.raises(FrozenInstanceError):
        check.key = "changed"  # type: ignore[misc]


def test_registered_checks_are_in_explicit_canonical_order() -> None:
    checks = tuple(item.check for item in registered_checks())
    assert [check.stable_order for check in checks] == sorted(check.stable_order for check in checks)
    assert [check.key for check in checks] == [
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
        "runtime_task_governance_invariant",
    ]


def test_artifact_hash_excludes_metadata_and_is_stable() -> None:
    check = CertificationCheck("sample", "unit", "sample check", 1)
    result = CertificationResult(check=check, passed=True)
    first = CertificationArtifact(results=(result,), metadata={"commit": "abc"})
    second = CertificationArtifact(results=(result,), metadata={"commit": "def"})
    assert first.artifact_hash == second.artifact_hash
    assert first.to_dict()["artifact_hash"] == second.to_dict()["artifact_hash"]


def test_runner_writes_canonical_artifact(tmp_path: Path, monkeypatch) -> None:
    check = CertificationCheck("sample", "unit", "sample check", 1)
    result = CertificationResult(check=check, passed=True)

    monkeypatch.setattr(
        "src.tests.certification.certification_runner.run_registered_checks",
        lambda: (result,),
    )

    artifact_path = tmp_path / "artifact.json"
    artifact = CertificationRunner(artifact_path=artifact_path).run()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert artifact.passed is True
    assert payload["artifact_hash"] == artifact.artifact_hash
    assert payload["results"][0]["check"]["key"] == "sample"


def test_runtime_task_governance_checks(tmp_path: Path) -> None:
    from src.tests.certification.runtime_task_governance_checks import check_runtime_task_governance
    
    # 1. Empty/no contracts dir should pass
    passed, detail = check_runtime_task_governance(tmp_path)
    assert passed is True
    
    # 2. Setup mock directories
    contracts_dir = tmp_path / "ai_runtime" / "contracts"
    inbox_dir = tmp_path / "ai_runtime" / "inbox"
    reports_dir = tmp_path / "ai_runtime" / "reports"
    contracts_dir.mkdir(parents=True)
    inbox_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    
    # 3. Legacy task <= 96 should be exempt (even if request/evidence are missing)
    legacy_contract = contracts_dir / "TASK-096.json"
    legacy_contract.write_text("{}", encoding="utf-8")
    passed, detail = check_runtime_task_governance(tmp_path)
    assert passed is True
    
    # 4. Governed task > 96 with contract but no inbox request should fail
    governed_contract = contracts_dir / "TASK-097.json"
    governed_contract.write_text("{}", encoding="utf-8")
    passed, detail = check_runtime_task_governance(tmp_path)
    assert passed is False
    assert "missing matching controller request" in detail
    
    # 5. Adding inbox request should pass (in-progress state)
    inbox_req = inbox_dir / "TASK-097-controller-request.md"
    inbox_req.write_text("mock request", encoding="utf-8")
    passed, detail = check_runtime_task_governance(tmp_path)
    assert passed is True
    
    # 6. Completed task (evidence file exists) but missing other reports should fail
    evidence_file = reports_dir / "TASK-097-evidence.json"
    evidence_file.write_text("{}", encoding="utf-8")
    passed, detail = check_runtime_task_governance(tmp_path)
    assert passed is False
    assert "missing required" in detail

