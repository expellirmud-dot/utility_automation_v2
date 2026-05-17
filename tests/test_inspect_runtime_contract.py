import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess
from datetime import datetime, timedelta
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_runtime_dirs():
    tmpdir = tempfile.mkdtemp()
    contracts_dir = os.path.join(tmpdir, "contracts")
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(contracts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    serializer = ExecutionContractSerializer()

    now = datetime.now()
    active_contract = {
        "contract_id": "CONT-TEST-001",
        "task_id": "TASK-101",
        "actor_id": "WORKER-01",
        "scope": {
            "allowed_read_paths": ["src/"],
            "allowed_write_paths": ["src/"]
        },
        "expected_outputs": ["src/foo.py"],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=60)).isoformat(),
        "metadata": {}
    }
    with open(os.path.join(contracts_dir, "TASK-101.json"), "w", encoding="utf-8") as f:
        json.dump(active_contract, f)

    expired_contract = {
        "contract_id": "CONT-TEST-002",
        "task_id": "TASK-102",
        "actor_id": "WORKER-01",
        "scope": {
            "allowed_read_paths": ["src/"],
            "allowed_write_paths": ["src/"]
        },
        "expected_outputs": ["src/foo.py"],
        "created_at": (now - timedelta(minutes=120)).isoformat(),
        "expires_at": (now - timedelta(minutes=60)).isoformat(),
        "metadata": {}
    }
    with open(os.path.join(contracts_dir, "TASK-102.json"), "w", encoding="utf-8") as f:
        json.dump(expired_contract, f)

    completed_contract = {
        "contract_id": "CONT-TEST-003",
        "task_id": "TASK-103",
        "actor_id": "WORKER-01",
        "scope": {
            "allowed_read_paths": ["src/"],
            "allowed_write_paths": ["src/"]
        },
        "expected_outputs": ["src/foo.py"],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=60)).isoformat(),
        "metadata": {}
    }
    with open(os.path.join(contracts_dir, "TASK-103.json"), "w", encoding="utf-8") as f:
        json.dump(completed_contract, f)

    evidence = {
        "contract_id": "CONT-TEST-003",
        "worker_id": "WORKER-01",
        "actual_outputs": ["src/foo.py"],
        "execution_trace": [],
        "completion_timestamp": now.isoformat(),
        "status": "SUCCESS"
    }
    with open(os.path.join(reports_dir, "TASK-103-evidence.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f)

    yield contracts_dir, reports_dir
    shutil.rmtree(tmpdir)


def test_inspect_missing_contract(temp_runtime_dirs):
    contracts_dir, reports_dir = temp_runtime_dirs
    script = "src/tools/runtime/inspect_runtime_contract.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-999",
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["state"] == "ISSUANCE_PENDING"
    assert data["contract_id"] is None


def test_inspect_active_contract(temp_runtime_dirs):
    contracts_dir, reports_dir = temp_runtime_dirs
    script = "src/tools/runtime/inspect_runtime_contract.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-101",
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["state"] == "ACTIVE"
    assert data["contract_id"] == "CONT-TEST-001"
    assert data["evidence_found"] is False


def test_inspect_expired_contract(temp_runtime_dirs):
    contracts_dir, reports_dir = temp_runtime_dirs
    script = "src/tools/runtime/inspect_runtime_contract.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-102",
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["state"] == "EXPIRED"
    assert data["contract_id"] == "CONT-TEST-002"


def test_inspect_completed_contract(temp_runtime_dirs):
    contracts_dir, reports_dir = temp_runtime_dirs
    script = "src/tools/runtime/inspect_runtime_contract.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-103",
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["state"] == "VALIDATED_COMPLETION"
    assert data["contract_id"] == "CONT-TEST-003"
    assert data["evidence_found"] is True
