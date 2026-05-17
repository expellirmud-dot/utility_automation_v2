import pytest
from datetime import datetime, timedelta
from src.services.governance.execution_contract.execution_contract_models import (
    ExecutionContract, 
    ExecutionScope, 
    CompletionEvidence
)

def test_execution_scope_creation():
    scope = ExecutionScope(
        allowed_read_paths={"file1.txt", "file2.txt"},
        allowed_write_paths={"out.txt"},
        allowed_commands=("ls", "grep"),
        forbidden_patterns=("rm -rf", "sudo")
    )
    assert "file1.txt" in scope.allowed_read_paths
    assert "out.txt" in scope.allowed_write_paths
    assert "ls" in scope.allowed_commands
    assert "sudo" in scope.forbidden_patterns

def test_execution_contract_creation():
    scope = ExecutionScope(allowed_read_paths={"in.txt"}, allowed_write_paths={"out.txt"})
    now = datetime.now()
    contract = ExecutionContract(
        contract_id="C-123",
        task_id="T-456",
        actor_id="A-789",
        scope=scope,
        expected_outputs=["out.txt"],
        created_at=now,
        expires_at=now + timedelta(hours=1)
    )
    assert contract.contract_id == "C-123"
    assert contract.task_id == "T-456"
    assert "out.txt" in contract.expected_outputs

def test_completion_evidence_creation():
    evidence = CompletionEvidence(
        contract_id="C-123",
        worker_id="W-001",
        actual_outputs=["out.txt"],
        execution_trace=[{"action": "read", "path": "in.txt"}, {"action": "write", "path": "out.txt"}],
        completion_timestamp=datetime.now(),
        status="SUCCESS"
    )
    assert evidence.contract_id == "C-123"
    assert "out.txt" in evidence.actual_outputs
    assert evidence.status == "SUCCESS"
