from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass(frozen=True)
class GuardResult:
    """
    Deterministic result of a Runtime Contract Guard check.
    """
    is_allowed: bool
    task_id: str
    worker_id: str
    contract_id: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
