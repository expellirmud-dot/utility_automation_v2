from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from src.tests.certification.certification_checks import registered_checks
from src.tests.certification.certification_models import (
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
