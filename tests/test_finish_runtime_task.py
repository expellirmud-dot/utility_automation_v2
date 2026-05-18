import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_finish_dirs():
    tmpdir = tempfile.mkdtemp()
    contracts_dir = os.path.join(tmpdir, "contracts")
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(contracts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    task_id = "TASK-888"
    worker_id = "WORKER-01"
    contract_file = os.path.join(contracts_dir, f"{task_id}.json")
    actual_out_file = os.path.join(tmpdir, "output.py")
    with open(actual_out_file, "w", encoding="utf-8") as f:
        f.write("# Actual output")

    # Mock contract
    contract_data = {
        "contract_id": "CONT-888",
        "task_id": task_id,
        "actor_id": worker_id,
        "created_at": "2026-05-18T00:00:00.000000",
        "expires_at": "2026-05-19T00:00:00.000000",
        "scope": {
            "allowed_read_paths": ["."],
            "allowed_write_paths": ["."],
            "allowed_commands": [],
            "forbidden_patterns": []
        },
        "expected_outputs": ["output.py"],
        "metadata": {}
    }
    with open(contract_file, "w", encoding="utf-8") as f:
        json.dump(contract_data, f)

    # Mock transcript with canonical headings
    with open(os.path.join(reports_dir, f"{task_id}-execution-transcript.md"), "w", encoding="utf-8") as f:
        f.write("""# Execution Transcript
## Task identification
TASK-888
## Read-first inspection
Checked
## Files inspected
output.py
## Files changed
output.py
## Commands executed
none
## Validation summary
passed
## Notes
none
""")

    # Mock tool trace
    with open(os.path.join(reports_dir, f"{task_id}-tool-trace.json"), "w", encoding="utf-8") as f:
        json.dump({"schema_version": "runtime-tool-trace-v1", "task_id": task_id, "worker_id": worker_id, "events": []}, f)

    # Mock worker report with canonical headings
    with open(os.path.join(reports_dir, f"{task_id}-worker-report.md"), "w", encoding="utf-8") as f:
        f.write("""# Worker Report
## Objective
Mock
## Scope completed
Mock
## Artifacts produced
output.py
## Validation results
Passed
## Risks
None
## Controller handoff
Ready
""")

    # Mock validation output
    with open(os.path.join(reports_dir, f"{task_id}-validation-output.txt"), "w", encoding="utf-8") as f:
        f.write("492 passed")

    yield tmpdir, contracts_dir, reports_dir, task_id, worker_id, actual_out_file
    shutil.rmtree(tmpdir)


def test_finish_runtime_task_success(temp_finish_dirs):
    tmpdir, contracts_dir, reports_dir, task_id, worker_id, actual_out_file = temp_finish_dirs
    script = "src/tools/runtime/finish_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--worker-id", worker_id,
        "--actual-output", "output.py",
        "--reports-dir", reports_dir,
        "--contracts-dir", contracts_dir,
        "--root-dir", tmpdir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "SUCCESS"
    assert data["task_id"] == task_id
    assert data["contract_id"] == "CONT-888"
    assert data["evidence_hash"] is not None
    assert data["lifecycle_state"] == "VALIDATED_COMPLETION"
    assert "controller_commit_package" in data
    assert os.path.exists(os.path.join(reports_dir, f"{task_id}-evidence.json"))
    assert os.path.exists(os.path.join(reports_dir, f"{task_id}-runtime-manifest.json"))


def test_finish_runtime_task_missing_contract(temp_finish_dirs):
    tmpdir, contracts_dir, reports_dir, _, worker_id, _ = temp_finish_dirs
    script = "src/tools/runtime/finish_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-MISSING",
        "--worker-id", worker_id,
        "--actual-output", "output.py",
        "--reports-dir", reports_dir,
        "--contracts-dir", contracts_dir,
        "--root-dir", tmpdir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["status"] == "FAILED"
    assert data["step"] == "locate_contract"


def test_finish_runtime_task_missing_reports(temp_finish_dirs):
    tmpdir, contracts_dir, reports_dir, task_id, worker_id, _ = temp_finish_dirs
    # Delete tool trace to trigger bundle validation failure
    os.remove(os.path.join(reports_dir, f"{task_id}-tool-trace.json"))

    script = "src/tools/runtime/finish_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--worker-id", worker_id,
        "--actual-output", "output.py",
        "--reports-dir", reports_dir,
        "--contracts-dir", contracts_dir,
        "--root-dir", tmpdir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["status"] == "FAILED"
    assert data["step"] == "validate_runtime_artifact_bundle"
