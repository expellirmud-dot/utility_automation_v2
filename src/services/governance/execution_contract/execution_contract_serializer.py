import json
from typing import Any, Dict
from datetime import datetime
from src.services.governance.policy_graph.policy_version import canonical_json, stable_hash
from src.services.governance.execution_contract.execution_contract_models import (
    ExecutionContract, 
    ExecutionScope, 
    CompletionEvidence
)

class ExecutionContractSerializer:
    """
    Handles deterministic serialization of governance contracts and evidence.
    """
    
    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        if hasattr(obj, "__dict__"):
            data = obj.__dict__.copy()
            for k, v in data.items():
                if isinstance(v, (set, tuple)):
                    data[k] = sorted(list(v))
                elif isinstance(v, datetime):
                    data[k] = v.isoformat()
                elif hasattr(v, "__dict__"):
                    data[k] = ExecutionContractSerializer.to_dict(v)
            return data
        return obj

    @classmethod
    def serialize(cls, obj: Any) -> str:
        """Returns a deterministic JSON string."""
        return canonical_json(cls.to_dict(obj))

    @classmethod
    def compute_hash(cls, obj: Any) -> str:
        """Returns a stable SHA-256 hash of the object."""
        return stable_hash(cls.to_dict(obj))

    @staticmethod
    def deserialize_contract(data: Dict[str, Any]) -> ExecutionContract:
        scope_data = data["scope"]
        scope = ExecutionScope(
            allowed_read_paths=set(scope_data.get("allowed_read_paths", [])),
            allowed_write_paths=set(scope_data.get("allowed_write_paths", [])),
            allowed_commands=tuple(scope_data.get("allowed_commands", [])),
            forbidden_patterns=tuple(scope_data.get("forbidden_patterns", [])),
            max_duration_seconds=scope_data.get("max_duration_seconds")
        )
        return ExecutionContract(
            contract_id=data["contract_id"],
            task_id=data["task_id"],
            actor_id=data["actor_id"],
            scope=scope,
            expected_outputs=data["expected_outputs"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            signature=data.get("signature"),
            metadata=data.get("metadata", {})
        )

    @staticmethod
    def deserialize_evidence(data: Dict[str, Any]) -> CompletionEvidence:
        return CompletionEvidence(
            contract_id=data["contract_id"],
            worker_id=data["worker_id"],
            actual_outputs=data["actual_outputs"],
            execution_trace=data["execution_trace"],
            completion_timestamp=datetime.fromisoformat(data["completion_timestamp"]),
            status=data["status"],
            evidence_hash=data.get("evidence_hash")
        )
