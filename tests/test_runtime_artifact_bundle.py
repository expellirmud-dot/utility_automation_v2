import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess
from src.services.governance.execution_contract.artifact_bundle_validator import ArtifactBundleValidator


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_env():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def setup_valid_bundle(root_dir: str, task_id: str, sub_dir: str = "reports") -> str:
    reports_dir = os.path.join(root_dir, sub_dir)
    os.makedirs(reports_dir, exist_ok=True)
    names = ArtifactBundleValidator.get_canonical_names(task_id)

    with open(os.path.join(reports_dir, names["execution_transcript"]), "w", encoding="utf-8") as f:
        f.write("# Transcript\n## Task identification\n1\n## Read-first inspection\n2\n## Files inspected\n3\n## Files changed\n4\n## Commands executed\n5\n## Validation summary\n6\n## Notes\n7")

    with open(os.path.join(reports_dir, names["tool_trace"]), "w", encoding="utf-8") as f:
        json.dump({"schema_version": "runtime-tool-trace-v1", "task_id": task_id, "events": []}, f)

    with open(os.path.join(reports_dir, names["worker_report"]), "w", encoding="utf-8") as f:
        f.write("# Report\n## Objective\n1\n## Scope completed\n2\n## Artifacts produced\n3\n## Validation results\n4\n## Risks\n5\n## Controller handoff\n6")

    with open(os.path.join(reports_dir, names["validation_output"]), "w", encoding="utf-8") as f:
        f.write("pytest passed")

    return sub_dir


def test_validator_validate_bundle_success(temp_env):
    task_id = "TASK-BUN-01"
    sub_dir = setup_valid_bundle(temp_env, task_id)

    validator = ArtifactBundleValidator(task_id=task_id, root_dir=temp_env)
    res = validator.validate_bundle(reports_dir=sub_dir)

    assert res["is_valid"] is True
    assert res["task_id"] == task_id
    assert len(res["validated_artifacts"]) == 4


def test_validator_generate_manifest(temp_env):
    task_id = "TASK-BUN-02"
    sub_dir = setup_valid_bundle(temp_env, task_id)

    validator = ArtifactBundleValidator(task_id=task_id, root_dir=temp_env)
    manifest = validator.generate_manifest(reports_dir=sub_dir, save=True)

    assert manifest["task_id"] == task_id
    assert "execution_transcript" in manifest["artifacts"]
    assert "execution_transcript" in manifest["hashes"]

    # Verify manifest file saved and is valid JSON
    manifest_file = os.path.join(temp_env, sub_dir, f"{task_id}-runtime-manifest.json")
    assert os.path.exists(manifest_file)
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["task_id"] == task_id


def test_cli_validate_bundle_success(temp_env):
    task_id = "TASK-CLI-01"
    sub_dir = setup_valid_bundle(temp_env, task_id)

    script = "src/tools/runtime/validate_runtime_artifact_bundle.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--reports-dir", sub_dir,
        "--generate-manifest",
        "--root-dir", temp_env
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    data = json.loads(res.stdout)
    assert data["is_valid"] is True
    assert "manifest" in data
    assert data["manifest"]["task_id"] == task_id
