from datetime import datetime, timedelta
import uuid
from typing import List, Set, Tuple, Optional, Dict, Any
from src.services.governance.execution_contract.execution_contract_models import (
    ExecutionContract, 
    ExecutionScope
)

class ExecutionContractBuilder:
    """
    Provides a fluent interface for constructing deterministic execution contracts.
    """
    
    def __init__(self, task_id: str, actor_id: str):
        self.task_id = task_id
        self.actor_id = actor_id
        self._read_paths: Set[str] = set()
        self._write_paths: Set[str] = set()
        self._commands: Set[str] = set()
        self._forbidden: Set[str] = set()
        self._outputs: List[str] = []
        self._duration: Optional[int] = None
        self._metadata: Dict[str, Any] = {}

    def allow_read(self, paths: List[str]) -> "ExecutionContractBuilder":
        self._read_paths.update(paths)
        return self

    def allow_write(self, paths: List[str]) -> "ExecutionContractBuilder":
        self._write_paths.update(paths)
        return self

    def allow_command(self, command: str) -> "ExecutionContractBuilder":
        self._commands.add(command)
        return self

    def forbid_pattern(self, pattern: str) -> "ExecutionContractBuilder":
        self._forbidden.add(pattern)
        return self

    def expect_output(self, path: str) -> "ExecutionContractBuilder":
        self._outputs.append(path)
        return self

    def set_duration(self, seconds: int) -> "ExecutionContractBuilder":
        self._duration = seconds
        return self

    def set_metadata(self, key: str, value: Any) -> "ExecutionContractBuilder":
        self._metadata[key] = value
        return self

    def build(self, validity_duration_minutes: int = 60) -> ExecutionContract:
        now = datetime.now()
        
        scope = ExecutionScope(
            allowed_read_paths=self._read_paths,
            allowed_write_paths=self._write_paths,
            allowed_commands=tuple(sorted(list(self._commands))),
            forbidden_patterns=tuple(sorted(list(self._forbidden))),
            max_duration_seconds=self._duration
        )
        
        return ExecutionContract(
            contract_id=f"CONT-{uuid.uuid4().hex[:8].upper()}",
            task_id=self.task_id,
            actor_id=self.actor_id,
            scope=scope,
            expected_outputs=self._outputs,
            created_at=now,
            expires_at=now + timedelta(minutes=validity_duration_minutes),
            metadata=self._metadata
        )
