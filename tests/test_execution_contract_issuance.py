import pytest
import os
import shutil
from datetime import datetime, timedelta
from src.services.governance.execution_contract.execution_contract_issuance_service import ExecutionContractIssuanceService
from src.services.governance.execution_contract.execution_contract_models import ExecutionContract

TEST_CONTRACTS_DIR = "tests/test_contracts"

@pytest.fixture
def issuance_service():
    # Cleanup and ensure directory exists for testing (since service fails closed)
    if os.path.exists(TEST_CONTRACTS_DIR):
        shutil.rmtree(TEST_CONTRACTS_DIR)
    os.makedirs(TEST_CONTRACTS_DIR)
    
    service = ExecutionContractIssuanceService(contracts_dir=TEST_CONTRACTS_DIR)
    yield service
    
    # Cleanup after test
    if os.path.exists(TEST_CONTRACTS_DIR):
        shutil.rmtree(TEST_CONTRACTS_DIR)

def test_issue_contract_success(issuance_service):
    task_id = "TASK-073-TEST"
    actor_id = "worker-1"
    read_paths = ["src/services/governance/"]
    write_paths = ["ai_runtime/reports/"]
    expected_outputs = ["ai_runtime/reports/test_report.md"]
    
    contract = issuance_service.issue_contract(
        task_id=task_id,
        actor_id=actor_id,
        read_paths=read_paths,
        write_paths=write_paths,
        expected_outputs=expected_outputs
    )
    
    assert isinstance(contract, ExecutionContract)
    assert contract.task_id == task_id
    assert contract.actor_id == actor_id
    assert set(read_paths) == contract.scope.allowed_read_paths
    assert set(write_paths) == contract.scope.allowed_write_paths
    assert expected_outputs == contract.expected_outputs
    
    # Verify persistence via filesystem directly (since retrieval helper is removed)
    file_path = os.path.join(TEST_CONTRACTS_DIR, f"{task_id}.json")
    assert os.path.exists(file_path)

def test_issue_contract_determinism(issuance_service):
    task_id = "TASK-DET-01"
    actor_id = "worker-1"
    ref_time = datetime(2026, 5, 18, 12, 0, 0)
    contract_id = "CONT-DET-001"
    
    params = {
        "task_id": task_id,
        "actor_id": actor_id,
        "read_paths": ["tests/read_path"],
        "write_paths": ["tests/write_path"],
        "expected_outputs": ["tests/write_path/out.txt"],
        "reference_time": ref_time,
        "contract_id": contract_id
    }
    
    contract1 = issuance_service.issue_contract(**params)
    
    # Reset dir to ensure we aren't just reading the same file
    shutil.rmtree(TEST_CONTRACTS_DIR)
    os.makedirs(TEST_CONTRACTS_DIR)
    
    contract2 = issuance_service.issue_contract(**params)
    
    assert contract1.contract_id == contract2.contract_id
    assert contract1.created_at == contract2.created_at
    assert contract1.expires_at == contract2.expires_at
    
    # Compare serialized content
    from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
    serializer = ExecutionContractSerializer()
    assert serializer.serialize(contract1) == serializer.serialize(contract2)

def test_issue_contract_complex_scope(issuance_service):
    task_id = "TASK-COMPLEX"
    actor_id = "worker-1"
    
    contract = issuance_service.issue_contract(
        task_id=task_id,
        actor_id=actor_id,
        read_paths=["tests/read/1", "tests/read/2"],
        write_paths=["tests/write/1"],
        expected_outputs=["tests/write/1/out.txt"],
        commands=["ls", "grep"],
        forbidden_patterns=["rm -rf", "chmod"],
        metadata={"priority": "high", "reason": "critical-fix"}
    )
    
    assert "ls" in contract.scope.allowed_commands
    assert "grep" in contract.scope.allowed_commands
    assert "rm -rf" in contract.scope.forbidden_patterns
    assert contract.metadata["priority"] == "high"
