import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.services.governance.execution_contract.execution_contract_models import ExecutionContract
from src.services.governance.execution_contract.execution_contract_builder import ExecutionContractBuilder
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer

class ExecutionContractIssuanceService:
    """
    Service responsible for the deterministic issuance and persistence of execution contracts.
    """

    def __init__(self, contracts_dir: str = "ai_runtime/contracts"):
        self.contracts_dir = contracts_dir
        self.serializer = ExecutionContractSerializer()

    def issue_contract(
        self, 
        task_id: str, 
        actor_id: str, 
        read_paths: List[str], 
        write_paths: List[str], 
        expected_outputs: List[str], 
        commands: Optional[List[str]] = None, 
        forbidden_patterns: Optional[List[str]] = None,
        validity_duration_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None,
        reference_time: Optional[datetime] = None,
        contract_id: Optional[str] = None
    ) -> ExecutionContract:
        """
        Builds, persists, and returns a deterministic ExecutionContract.
        """
        builder = ExecutionContractBuilder(task_id, actor_id)
        
        builder.allow_read(read_paths)
        builder.allow_write(write_paths)
        
        for output in expected_outputs:
            builder.expect_output(output)
            
        if commands:
            for cmd in commands:
                builder.allow_command(cmd)
                
        if forbidden_patterns:
            for pattern in forbidden_patterns:
                builder.forbid_pattern(pattern)
                
        if metadata:
            for k, v in metadata.items():
                builder.set_metadata(k, v)

        # Build the contract deterministically
        contract = builder.build(
            validity_duration_minutes=validity_duration_minutes,
            now=reference_time,
            contract_id=contract_id
        )

        # Persist to filesystem
        self._persist_contract(contract)

        return contract

    def _persist_contract(self, contract: ExecutionContract):
        """
        Saves the contract to the contracts directory as a deterministic JSON file.
        """
        if not os.path.isdir(self.contracts_dir):
            raise RuntimeError(f"Contracts directory does not exist: {self.contracts_dir}")

        file_path = os.path.join(self.contracts_dir, f"{contract.task_id}.json")
        
        # Use the serializer for deterministic JSON
        serialized_data = self.serializer.serialize(contract)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(serialized_data)
