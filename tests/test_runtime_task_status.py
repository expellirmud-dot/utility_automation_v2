import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_status_dirs():
    tmpdir = tempfile.mkdtemp()
    contracts_dir = os.path.join(tmpdir, "contracts")
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(contracts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    task_id1 = "TASK-001"
    contract_file1 = os.path.join(contracts_dir, f"{task_id1}.json")
    c1 = {
        "contract_id": "CONT-001",
        "task_id": task_id1,
        "actor_id": "WORKER-01",
        "created_at": "2026-05-18T00:00:00",
        "expires_at": "2026-05-19T00:00:00",
        "scope": {"allowed_read_paths": ["."], "allowed_write_paths": ["."], "allowed_commands": [], "forbidden_patterns": []},
        "expected_outputs": [],
        "metadata": {}
    }
    with open(contract_file1, "w", encoding="utf-8") as f:
        json.dump(c1, f)

    task_id2 = "TASK-002"
    contract_file2 = os.path.join(contracts_dir, f"{task_id2}.json")
    c2 = {
        "contract_id": "CONT-002",
        "task_id": task_id2,
        "actor_id": "WORKER-02",
        "created_at": "2020-01-01T00:00:00",
        "expires_at": "2020-01-02T00:00:00",
        "scope": {"allowed_read_paths": ["."], "allowed_write_paths": ["."], "allowed_commands": [], "forbidden_patterns": []},
        "expected_outputs": [],
        "metadata": {}
    }
    with open(contract_file2, "w", encoding="utf-8") as f:
        json.dump(c2, f)

    yield tmpdir, contracts_dir, reports_dir
    shutil.rmtree(tmpdir)


def test_runtime_task_status_json(temp_status_dirs):
    tmpdir, contracts_dir, reports_dir = temp_status_dirs
    script = "src/tools/runtime/runtime_task_status.py"

    cmd = [
        PYTHON_EXE, script,
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir,
        "--format", "json"
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["count"] == 2
    assert len(data["tasks"]) == 2
    task1 = [t for t in data["tasks"] if t["task_id"] == "TASK-001"][0]
    task2 = [t for t in data["tasks"] if t["task_id"] == "TASK-002"][0]
    assert task1["state"] == "ACTIVE"
    assert task2["state"] == "EXPIRED"


def test_runtime_task_status_table(temp_status_dirs):
    tmpdir, contracts_dir, reports_dir = temp_status_dirs
    script = "src/tools/runtime/runtime_task_status.py"

    cmd = [
        PYTHON_EXE, script,
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir,
        "--format", "table"
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    assert "TASK-001" in res.stdout
    assert "CONT-001" in res.stdout
    assert "TASK-002" in res.stdout
    assert "EXPIRED" in res.stdout
