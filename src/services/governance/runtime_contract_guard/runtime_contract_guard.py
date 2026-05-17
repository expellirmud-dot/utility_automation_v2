import os
import json
from datetime import datetime
from typing import Optional, List, Tuple
from src.services.governance.execution_contract.execution_contract_models import ExecutionContract
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.services.governance.execution_contract.execution_contract_validator import ExecutionContractValidator
from src.services.governance.runtime_contract_guard.runtime_contract_guard_models import GuardResult
from src.services.governance.runtime_contract_guard.runtime_contract_guard_exceptions import (
    ContractNotFoundError,
    ContractInvalidError,
    IdentityMismatchError,
    ScopeViolationError,
    GuardBlockedError
)

class RuntimeContractGuard:
    """
    Enforces that worker tasks proceed only if a valid execution contract exists.
    """
    
    def __init__(self, contracts_dir: str = "ai_runtime/contracts"):
        self.contracts_dir = contracts_dir
        self.validator = ExecutionContractValidator()
        self.serializer = ExecutionContractSerializer()

    def _get_contract_path(self, task_id: str) -> str:
        # Assuming contracts are named TASK-XXX.json or similar
        # For now, we look for a file matching the task_id pattern in the directory
        return os.path.join(self.contracts_dir, f"{task_id}.json")

    def check_execution_readiness(self, task_id: str, worker_id: str) -> GuardResult:
        """
        Validates if a worker is allowed to start implementation for a given task.
        """
        try:
            contract_path = self._get_contract_path(task_id)
            
            if not os.path.exists(contract_path):
                raise ContractNotFoundError(f"No execution contract found at {contract_path}")

            with open(contract_path, 'r') as f:
                data = json.load(f)
            
            contract = self.serializer.deserialize_contract(data)
            
            # 1. Basic Structural and Expiry Validation
            self.validator.validate_contract(contract)
            
            # 2. Task ID Match
            if contract.task_id != task_id:
                raise IdentityMismatchError(f"Contract task_id {contract.task_id} does not match requested task_id {task_id}")
            
            # 3. Worker/Actor ID Match
            if contract.actor_id != worker_id:
                raise IdentityMismatchError(f"Contract actor_id {contract.actor_id} does not match worker_id {worker_id}")
            
            return GuardResult(
                is_allowed=True,
                task_id=task_id,
                worker_id=worker_id,
                contract_id=contract.contract_id,
                reason="Execution contract validated successfully."
            )

        except GuardBlockedError as e:
            return GuardResult(
                is_allowed=False,
                task_id=task_id,
                worker_id=worker_id,
                reason=str(e)
            )
        except Exception as e:
            # Fail-closed on any unexpected error
            return GuardResult(
                is_allowed=False,
                task_id=task_id,
                worker_id=worker_id,
                reason=f"Unexpected guard failure: {str(e)}"
            )

    def validate_action(self, task_id: str, worker_id: str, action_type: str, path: str, command: Optional[str] = None) -> GuardResult:
        """
        Validates a specific action against the contract.
        """
        try:
            # First, ensure the worker is ready to execute
            readiness = self.check_execution_readiness(task_id, worker_id)
            if not readiness.is_allowed:
                return readiness

            contract_path = self._get_contract_path(task_id)
            with open(contract_path, 'r') as f:
                data = json.load(f)
                contract = self.serializer.deserialize_contract(data)

            # Validate action against scope
            self.validator.validate_execution_step(contract, action_type, path, command)
            
            return GuardResult(
                is_allowed=True,
                task_id=task_id,
                worker_id=worker_id,
                contract_id=contract.contract_id,
                reason=f"Action {action_type} on {path} allowed by contract."
            )

        except GuardBlockedError as e:
            return GuardResult(
                is_allowed=False,
                task_id=task_id,
                worker_id=worker_id,
                reason=str(e)
            )
        except Exception as e:
            return GuardResult(
                is_allowed=False,
                task_id=task_id,
                worker_id=worker_id,
                reason=f"Unexpected action validation failure: {str(e)}"
            )
