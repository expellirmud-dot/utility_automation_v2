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

def test_fail_closed_empty_scope():
    # Scope with nothing allowed should fail validation
    scope = ExecutionScope(allowed_read_paths=set(), allowed_write_paths=set())
    contract = ExecutionContract(
        contract_id="C-FAIL", task_id="T-FAIL", actor_id="A-FAIL", 
        scope=scope, expected_outputs=[], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    with pytest.raises(ContractValidationError, match="must allow at least one read or write path"):
        ExecutionContractValidator.validate_contract(contract)

def test_fail_closed_expired_contract():
    scope = ExecutionScope(allowed_read_paths={"in.txt"})
    now = datetime.now()
    contract = ExecutionContract(
        contract_id="C-EXPIRED", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=[], 
        created_at=now - timedelta(hours=2), expires_at=now - timedelta(hours=1)
    )
    with pytest.raises(ContractValidationError, match="has expired"):
        ExecutionContractValidator.validate_contract(contract)

def test_fail_closed_unauthorized_command():
    scope = ExecutionScope(allowed_commands=("ls",))
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=[], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    with pytest.raises(ScopeViolationError):
        ExecutionContractValidator.validate_execution_step(contract, "command", "bin", "wget")

def test_fail_closed_evidence_mismatch():
    scope = ExecutionScope(allowed_write_paths={"out.txt"})
    contract = ExecutionContract(
        contract_id="C-1", task_id="T-1", actor_id="A-1", 
        scope=scope, expected_outputs=["out.txt"], 
        created_at=datetime.now(), expires_at=datetime.now() + timedelta(hours=1)
    )
    # Evidence says SUCCESS but missing output
    evidence = CompletionEvidence(
        contract_id="C-1", worker_id="W-1", actual_outputs=[],
        execution_trace=[], completion_timestamp=datetime.now(), status="SUCCESS"
    )
    with pytest.raises(EvidenceValidationError, match="Missing expected outputs"):
        ExecutionContractValidator.validate_completion(contract, evidence)
