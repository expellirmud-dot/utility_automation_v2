from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime

@dataclass(frozen=True)
class ExecutionScope:
    """
    Defines the strict boundaries of what a worker is allowed to do.
    """
    allowed_read_paths: Set[str] = field(default_factory=set)
    allowed_write_paths: Set[str] = field(default_factory=set)
    allowed_commands: Tuple[str, ...] = field(default_factory=tuple)
    forbidden_patterns: Tuple[str, ...] = field(default_factory=tuple)
    max_duration_seconds: Optional[int] = None
    
    def __post_init__(self):
        # Ensure sets are converted to sorted tuples for determinism if needed in serialization
        # But since this is a dataclass, we keep them as sets for O(1) lookup during validation
        pass

@dataclass(frozen=True)
class ExecutionContract:
    """
    The authoritative agreement between the Controller and the Worker.
    """
    contract_id: str
    task_id: str
    actor_id: str
    scope: ExecutionScope
    expected_outputs: List[str]
    created_at: datetime
    expires_at: datetime
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CompletionEvidence:
    """
    The evidence produced by the worker to prove contract fulfillment.
    """
    contract_id: str
    worker_id: str
    actual_outputs: List[str]
    execution_trace: List[Dict[str, Any]]
    completion_timestamp: datetime
    status: str # SUCCESS, FAILED, PARTIAL
    evidence_hash: Optional[str] = None
