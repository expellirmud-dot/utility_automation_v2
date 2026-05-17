import pytest
from datetime import datetime, timedelta
from src.services.governance.execution_contract.execution_contract_models import (
    ExecutionContract, 
    ExecutionScope, 
    CompletionEvidence
)
from src.services.governance.execution_contract.execution_contract_validator import (
    ExecutionContractValidator, 
    ContractValidationError, 
    ScopeViolationError, 
    EvidenceValidationError
)

def test_validate_contract_success():
    scope = ExecutionScope(allowed_read_paths={"in.txt"}, allowed_write_paths={"out.txt"})
    now = datetime.now()
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=["out.txt"],
        created_at=now, expires_at=now + timedelta(hours=1)
    )
    # Should not raise
    ExecutionContractValidator.validate_contract(contract)

def test_validate_contract_expired():
    scope = ExecutionScope(allowed_read_paths={"in.txt"})
    now = datetime.now()
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=[],
        created_at=now - timedelta(hours=2), expires_at=now - timedelta(hours=1)
    )
    with pytest.raises(ContractValidationError, match="has expired"):
        ExecutionContractValidator.validate_contract(contract)

def test_validate_execution_step_success():
    scope = ExecutionScope(
        allowed_read_paths={"in.txt"}, 
        allowed_write_paths={"out.txt"}, 
        allowed_commands=("ls",)
    )
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=[], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    # All these should pass
    ExecutionContractValidator.validate_execution_step(contract, "read", "in.txt")
    ExecutionContractValidator.validate_execution_step(contract, "write", "out.txt")
    ExecutionContractValidator.validate_execution_step(contract, "command", "some_path", "ls")

def test_validate_execution_step_violations():
    scope = ExecutionScope(
        allowed_read_paths={"in.txt"}, 
        allowed_write_paths={"out.txt"}, 
        allowed_commands=("ls",),
        forbidden_patterns=("rm -rf",)
    )
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=[], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    
    with pytest.raises(ScopeViolationError, match="Read access denied"):
        ExecutionContractValidator.validate_execution_step(contract, "read", "secret.txt")
        
    with pytest.raises(ScopeViolationError, match="Write access denied"):
        ExecutionContractValidator.validate_execution_step(contract, "write", "root.conf")
        
    with pytest.raises(ScopeViolationError, match="Command execution denied"):
        ExecutionContractValidator.validate_execution_step(contract, "command", "bin", "sudo")
        
    with pytest.raises(ScopeViolationError, match="violates forbidden pattern"):
        ExecutionContractValidator.validate_execution_step(contract, "command", "home", "rm -rf /")

def test_validate_completion_success():
    scope = ExecutionScope(allowed_read_paths={"in.txt"}, allowed_write_paths={"out.txt"})
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=["out.txt"], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    evidence = CompletionEvidence(
        contract_id="C-1", worker_id="W-1", actual_outputs=["out.txt"],
        execution_trace=[{"action": "read", "path": "in.txt"}, {"action": "write", "path": "out.txt"}],
        completion_timestamp=datetime.now(), status="SUCCESS"
    )
    # Should pass
    ExecutionContractValidator.validate_completion(contract, evidence)

def test_validate_completion_failures():
    scope = ExecutionScope(allowed_read_paths={"in.txt"}, allowed_write_paths={"out.txt"})
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=["out.txt", "report.txt"], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    
    # Case 1: Wrong Contract ID
    evidence_wrong_id = CompletionEvidence(
        contract_id="C-WRONG", worker_id="W-1", actual_outputs=["out.txt"],
        execution_trace=[], completion_timestamp=datetime.now(), status="SUCCESS"
    )
    with pytest.raises(EvidenceValidationError, match="contract ID mismatch"):
        ExecutionContractValidator.validate_completion(contract, evidence_wrong_id)
        
    # Case 2: Missing Output
    evidence_missing_out = CompletionEvidence(
        contract_id="C-1", worker_id="W-1", actual_outputs=["out.txt"],
        execution_trace=[], completion_timestamp=datetime.now(), status="SUCCESS"
    )
    with pytest.raises(EvidenceValidationError, match="Missing expected outputs"):
        ExecutionContractValidator.validate_completion(contract, evidence_missing_out)
        
    # Case 3: Unauthorized write in trace
    evidence_unauth_write = CompletionEvidence(
        contract_id="C-1", worker_id="W-1", actual_outputs=["out.txt", "report.txt"],
        execution_trace=[{"action": "write", "path": "secret.txt"}],
        completion_timestamp=datetime.now(), status="SUCCESS"
    )
    with pytest.raises(ScopeViolationError, match="Unauthorized write detected"):
        ExecutionContractValidator.validate_completion(contract, evidence_unauth_write)
