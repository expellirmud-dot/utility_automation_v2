from typing import List, Dict, Any, Optional
from datetime import datetime
from src.services.governance.execution_contract.execution_contract_models import (
    ExecutionContract, 
    CompletionEvidence
)
from src.services.governance.execution_contract.execution_contract_exceptions import (
    ContractValidationError, 
    ScopeViolationError, 
    EvidenceValidationError
)

class ExecutionContractValidator:
    """
    Enforces the boundaries of the Execution Contract.
    Implements fail-closed logic.
    """
    
    @staticmethod
    def validate_contract(contract: ExecutionContract, reference_time: Optional[datetime] = None):
        """
        Ensures the contract is structurally sound and not expired.
        Uses reference_time for deterministic replayability.
        """
        now = reference_time or datetime.now()
        
        if not contract.contract_id or not contract.task_id:
            raise ContractValidationError("Contract must have a valid ID and Task ID.")
        
        if now > contract.expires_at:
            raise ContractValidationError(f"Contract {contract.contract_id} has expired.")
            
        if not contract.scope.allowed_read_paths and not contract.scope.allowed_write_paths:
            raise ContractValidationError("Contract scope must allow at least one read or write path.")

    @staticmethod
    def _is_path_allowed(path: str, allowed_paths: set) -> bool:
        """
        Checks if a path is allowed using prefix matching.
        Prevents directory traversal attacks.
        """
        if ".." in path:
            return False
            
        # Exact match
        if path in allowed_paths:
            return True
            
        # Prefix match (directory allowance)
        for allowed in allowed_paths:
            if path.startswith(allowed) and (
                allowed.endswith("/") or 
                (len(path) > len(allowed) and path[len(allowed)] == "/")
            ):
                return True
        return False

    @staticmethod
    def validate_execution_step(contract: ExecutionContract, action_type: str, path: str, command: str = None):
        """
        Validates a single worker action against the contract scope.
        """
        # Check forbidden patterns first (Fail-Closed)
        for pattern in contract.scope.forbidden_patterns:
            if pattern in path or (command and pattern in command):
                raise ScopeViolationError(f"Action violates forbidden pattern: {pattern}")

        if action_type == "read":
            if not ExecutionContractValidator._is_path_allowed(path, contract.scope.allowed_read_paths):
                raise ScopeViolationError(f"Read access denied for path: {path}")
        
        elif action_type == "write":
            if not ExecutionContractValidator._is_path_allowed(path, contract.scope.allowed_write_paths):
                raise ScopeViolationError(f"Write access denied for path: {path}")
        
        elif action_type == "command":
            if command not in contract.scope.allowed_commands:
                raise ScopeViolationError(f"Command execution denied: {command}")

    @staticmethod
    def validate_completion(contract: ExecutionContract, evidence: CompletionEvidence):
        """
        Validates that the worker's completion evidence matches the contract's requirements.
        """
        if evidence.contract_id != contract.contract_id:
            raise EvidenceValidationError("Evidence contract ID mismatch.")
            
        if evidence.status != "SUCCESS":
            raise EvidenceValidationError(f"Worker reported non-success status: {evidence.status}")

        # Check for all expected outputs
        missing_outputs = [out for out in contract.expected_outputs if out not in evidence.actual_outputs]
        if missing_outputs:
            raise EvidenceValidationError(f"Missing expected outputs: {missing_outputs}")

        # Validate that no unauthorized writes occurred in the trace
        for step in evidence.execution_trace:
            if step.get("action") == "write":
                path = step.get("path")
                if not ExecutionContractValidator._is_path_allowed(path, contract.scope.allowed_write_paths):
                    raise ScopeViolationError(f"Unauthorized write detected in trace: {path}")
