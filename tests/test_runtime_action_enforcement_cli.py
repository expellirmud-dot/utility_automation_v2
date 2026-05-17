import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess
from src.services.governance.execution_contract.execution_contract_builder import ExecutionContractBuilder
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_contracts_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def setup_test_contract(dir_path: str, task_id: str, actor_id: str):
    builder = ExecutionContractBuilder(task_id=task_id, actor_id=actor_id)
    builder.allow_read(["src/", "tests/"])
    builder.allow_write(["src/tools/runtime/"])
    builder.allow_command("ls")
    contract = builder.build(validity_duration_minutes=60)
    serializer = ExecutionContractSerializer()

    with open(os.path.join(dir_path, f"{task_id}.json"), "w", encoding="utf-8") as f:
        f.write(serializer.serialize(contract))


def test_cli_allowed_write_action(temp_contracts_dir):
    task_id = "TASK-CLI-ACT-01"
    actor_id = "WORKER-01"
    setup_test_contract(temp_contracts_dir, task_id, actor_id)

    script = "src/tools/runtime/enforce_runtime_action.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--actor-id", actor_id,
        "--action-type", "write",
        "--path", "src/tools/runtime/new_tool.py",
        "--contracts-dir", temp_contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    data = json.loads(res.stdout)
    assert data["is_allowed"] is True
    assert data["task_id"] == task_id


def test_cli_blocked_write_action_fails(temp_contracts_dir):
    task_id = "TASK-CLI-ACT-02"
    actor_id = "WORKER-01"
    setup_test_contract(temp_contracts_dir, task_id, actor_id)

    script = "src/tools/runtime/enforce_runtime_action.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--actor-id", actor_id,
        "--action-type", "write",
        "--path", "secrets/key.txt",
        "--contracts-dir", temp_contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["is_allowed"] is False
    assert "Write access denied" in data["reason"]


def test_cli_blocked_command_fails(temp_contracts_dir):
    task_id = "TASK-CLI-ACT-03"
    actor_id = "WORKER-01"
    setup_test_contract(temp_contracts_dir, task_id, actor_id)

    script = "src/tools/runtime/enforce_runtime_action.py"
    cmd = [
        PYTHON_EXE, script,
        "--task-id", task_id,
        "--actor-id", actor_id,
        "--action-type", "command",
        "--command", "rm -rf /",
        "--contracts-dir", temp_contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["is_allowed"] is False
    assert "Command execution denied" in data["reason"]
