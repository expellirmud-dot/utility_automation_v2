import os
import sys
import json
import shutil
import pytest
import tempfile
import subprocess
from datetime import datetime

PYTHON_EXE = sys.executable

@pytest.fixture
def temp_contracts_env():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def run_cli_cmd(script_path: str, args: list, env: dict = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    full_env["PYTHONPATH"] = "."
    if env:
        full_env.update(env)
    cmd = [PYTHON_EXE, script_path] + args
    return subprocess.run(cmd, env=full_env, capture_output=True, text=True)

def test_issuance_cli_success(temp_contracts_env):
    script = "src/tools/runtime/issue_execution_contract.py"
    args = [
        "--task-id", "TASK-CLI-01",
        "--actor-id", "WORKER-CLI-01",
        "--allow-read", "src/", "tests/",
        "--allow-write", "ai_runtime/",
        "--expected-output", "ai_runtime/out.json",
        "--metadata", "env=prod", "priority=high",
        "--contracts-dir", temp_contracts_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 0, f"CLI failed: {res.stderr} {res.stdout}"
    
    data = json.loads(res.stdout)
    assert data["task_id"] == "TASK-CLI-01"
    assert data["actor_id"] == "WORKER-CLI-01"
    assert "src/" in data["scope"]["allowed_read_paths"]
    assert "ai_runtime/" in data["scope"]["allowed_write_paths"]
    assert data["expected_outputs"] == ["ai_runtime/out.json"]
    assert data["metadata"] == {"env": "prod", "priority": "high"}
    
    # Check persistence
    contract_file = os.path.join(temp_contracts_env, "TASK-CLI-01.json")
    assert os.path.exists(contract_file)

def test_issuance_cli_deterministic_replay(temp_contracts_env):
    script = "src/tools/runtime/issue_execution_contract.py"
    ref_time = "2026-05-18T12:00:00"
    contract_id = "CONT-DET-999"
    args = [
        "--task-id", "TASK-DET-01",
        "--actor-id", "WORKER-01",
        "--allow-read", "src/",
        "--allow-write", "ai_runtime/",
        "--expected-output", "ai_runtime/out.json",
        "--reference-time", ref_time,
        "--contract-id", contract_id,
        "--contracts-dir", temp_contracts_env
    ]
    res1 = run_cli_cmd(script, args)
    assert res1.returncode == 0
    
    # Replay
    shutil.rmtree(temp_contracts_env)
    os.makedirs(temp_contracts_env)
    
    res2 = run_cli_cmd(script, args)
    assert res2.returncode == 0
    assert res1.stdout.strip() == res2.stdout.strip()

def test_issuance_cli_missing_args(temp_contracts_env):
    script = "src/tools/runtime/issue_execution_contract.py"
    # No read/write paths
    args = [
        "--task-id", "TASK-FAIL-01",
        "--actor-id", "WORKER-01",
        "--expected-output", "ai_runtime/out.json",
        "--contracts-dir", temp_contracts_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["success"] is False
    assert "Contract scope must allow at least one read or write path" in data["error"]

def test_issuance_cli_malformed_metadata(temp_contracts_env):
    script = "src/tools/runtime/issue_execution_contract.py"
    args = [
        "--task-id", "TASK-META-FAIL",
        "--actor-id", "WORKER-01",
        "--allow-write", "ai_runtime/",
        "--expected-output", "ai_runtime/out.json",
        "--metadata", '{"broken_json: 123',
        "--contracts-dir", temp_contracts_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["success"] is False
    assert "Malformed JSON metadata" in data["error"]

def test_readiness_cli_success_and_failure(temp_contracts_env):
    issuance_script = "src/tools/runtime/issue_execution_contract.py"
    readiness_script = "src/tools/runtime/check_execution_readiness.py"
    
    # Issue contract first
    issue_args = [
        "--task-id", "TASK-READY-01",
        "--actor-id", "WORKER-READY",
        "--allow-write", "ai_runtime/",
        "--expected-output", "ai_runtime/out.json",
        "--contracts-dir", temp_contracts_env
    ]
    run_cli_cmd(issuance_script, issue_args)
    
    # Check readiness success
    ready_args = [
        "--task-id", "TASK-READY-01",
        "--actor-id", "WORKER-READY",
        "--contracts-dir", temp_contracts_env
    ]
    res_success = run_cli_cmd(readiness_script, ready_args)
    assert res_success.returncode == 0
    data_success = json.loads(res_success.stdout)
    assert data_success["is_allowed"] is True
    
    # Check readiness failure (actor mismatch)
    fail_args = [
        "--task-id", "TASK-READY-01",
        "--actor-id", "WORKER-WRONG",
        "--contracts-dir", temp_contracts_env
    ]
    res_fail = run_cli_cmd(readiness_script, fail_args)
    assert res_fail.returncode == 1
    data_fail = json.loads(res_fail.stdout)
    assert data_fail["is_allowed"] is False
    assert "actor_id" in data_fail["reason"]

def test_missing_contract_failure(temp_contracts_env):
    script = "src/tools/runtime/check_execution_readiness.py"
    args = [
        "--task-id", "TASK-NONEXISTENT",
        "--actor-id", "WORKER-01",
        "--contracts-dir", temp_contracts_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["is_allowed"] is False
    assert "No execution contract found" in data["reason"]

def test_completion_validation_success_and_failure(temp_contracts_env, tmp_path):
    issuance_script = "src/tools/runtime/issue_execution_contract.py"
    validation_script = "src/tools/runtime/validate_completion_evidence.py"
    
    task_id = "TASK-VAL-01"
    contract_id = "CONT-VAL-123"
    actor_id = "WORKER-VAL"
    
    # Issue contract
    issue_args = [
        "--task-id", task_id,
        "--actor-id", actor_id,
        "--allow-write", "ai_runtime/valid_dir/",
        "--expected-output", "ai_runtime/valid_dir/out.json",
        "--contract-id", contract_id,
        "--contracts-dir", temp_contracts_env
    ]
    run_cli_cmd(issuance_script, issue_args)
    
    # Create valid evidence JSON
    valid_evidence = {
        "contract_id": contract_id,
        "worker_id": actor_id,
        "actual_outputs": ["ai_runtime/valid_dir/out.json"],
        "execution_trace": [
            {"action": "write", "path": "ai_runtime/valid_dir/out.json"}
        ],
        "completion_timestamp": "2026-05-18T12:00:00",
        "status": "SUCCESS"
    }
    valid_evidence_file = tmp_path / "valid_evidence.json"
    valid_evidence_file.write_text(json.dumps(valid_evidence))
    
    # Validate success
    val_args = [
        "--task-id", task_id,
        "--evidence-file", str(valid_evidence_file),
        "--contracts-dir", temp_contracts_env
    ]
    res_val_success = run_cli_cmd(validation_script, val_args)
    assert res_val_success.returncode == 0
    data_val_success = json.loads(res_val_success.stdout)
    assert data_val_success["is_valid"] is True
    
    # Create unauthorized write evidence JSON
    unauth_evidence = {
        "contract_id": contract_id,
        "worker_id": actor_id,
        "actual_outputs": ["ai_runtime/valid_dir/out.json"],
        "execution_trace": [
            {"action": "write", "path": "ai_runtime/valid_dir/out.json"},
            {"action": "write", "path": "secrets/system_key.pem"}
        ],
        "completion_timestamp": "2026-05-18T12:00:00",
        "status": "SUCCESS"
    }
    unauth_evidence_file = tmp_path / "unauth_evidence.json"
    unauth_evidence_file.write_text(json.dumps(unauth_evidence))
    
    # Validate failure (unauthorized write)
    unauth_args = [
        "--task-id", task_id,
        "--evidence-file", str(unauth_evidence_file),
        "--contracts-dir", temp_contracts_env
    ]
    res_val_fail = run_cli_cmd(validation_script, unauth_args)
    assert res_val_fail.returncode == 1
    data_val_fail = json.loads(res_val_fail.stdout)
    assert data_val_fail["is_valid"] is False
    assert "Unauthorized write" in data_val_fail["reason"]
