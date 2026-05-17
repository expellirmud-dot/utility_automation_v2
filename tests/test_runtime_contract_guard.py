import pytest
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from src.services.governance.runtime_contract_guard.runtime_contract_guard import RuntimeContractGuard
from src.services.governance.execution_contract.execution_contract_builder import ExecutionContractBuilder
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer

@pytest.fixture
def temp_contracts_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture
def guard(temp_contracts_dir):
    return RuntimeContractGuard(contracts_dir=temp_contracts_dir)

@pytest.fixture
def serializer():
    return ExecutionContractSerializer()

def create_contract_file(dir_path, task_id, actor_id, read_paths=None, write_paths=None, commands=None, expires_in_mins=60):
    builder = ExecutionContractBuilder(task_id=task_id, actor_id=actor_id)
    
    # Ensure at least one path is allowed to satisfy ExecutionContractValidator
    if read_paths is None and write_paths is None:
        builder.allow_read(["ai_runtime/inbox"])
    else:
        if read_paths:
            builder.allow_read(read_paths)
        if write_paths:
            builder.allow_write(write_paths)
    
    if commands:
        for cmd in commands:
            builder.allow_command(cmd)
    
    contract = builder.build(validity_duration_minutes=expires_in_mins)
    serializer = ExecutionContractSerializer()
    content = serializer.serialize(contract)
    
    with open(os.path.join(dir_path, f"{task_id}.json"), 'w') as f:
        f.write(content)

def test_guard_blocks_missing_contract(guard):
    result = guard.check_execution_readiness("TASK-001", "WORKER-001")
    assert result.is_allowed is False
    assert "No execution contract found" in result.reason

def test_guard_allows_valid_contract(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001")
    result = guard.check_execution_readiness("TASK-001", "WORKER-001")
    assert result.is_allowed is True
    assert "validated successfully" in result.reason

def test_guard_blocks_task_id_mismatch(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001")
    result = guard.check_execution_readiness("TASK-002", "WORKER-001")
    assert result.is_allowed is False
    assert "No execution contract found" in result.reason # Because it looks for TASK-002.json

def test_guard_blocks_actor_id_mismatch(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-CORRECT")
    result = guard.check_execution_readiness("TASK-001", "WORKER-WRONG")
    assert result.is_allowed is False
    assert "actor_id" in result.reason

def test_guard_blocks_expired_contract(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001", expires_in_mins=-10)
    result = guard.check_execution_readiness("TASK-001", "WORKER-001")
    assert result.is_allowed is False
    assert "has expired" in result.reason

def test_action_validation_allowed(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001", write_paths=["src/main.py"])
    result = guard.validate_action("TASK-001", "WORKER-001", "write", "src/main.py")
    assert result.is_allowed is True

def test_action_validation_blocked_path(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001", write_paths=["src/main.py"])
    result = guard.validate_action("TASK-001", "WORKER-001", "write", "secrets/password.txt")
    assert result.is_allowed is False
    assert "Write access denied" in result.reason

def test_action_validation_blocked_command(guard, temp_contracts_dir):
    create_contract_file(temp_contracts_dir, "TASK-001", "WORKER-001", commands=["ls"])
    result = guard.validate_action("TASK-001", "WORKER-001", "command", "any", command="rm -rf /")
    assert result.is_allowed is False
    assert "Command execution denied" in result.reason
