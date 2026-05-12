from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class DomainEvent:
    event_id: str
    aggregate_id: str  # voucher_id
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    version: int
