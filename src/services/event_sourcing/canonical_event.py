from dataclasses import dataclass, field
from datetime import datetime
import uuid
import hashlib
import json
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class CanonicalEvent:
    event_id: str
    epoch: int
    seq_id: int
    timestamp: str
    actor: str
    type: str
    payload: Dict[str, Any]
    signature: str
    prev_hash: str
    global_chain_hash: str
    version: int = 1
    # NEW: Causal lineage for Byzantine-stability
    parent_event_ids: List[str] = field(default_factory=list)
    causal_depth: int = 0

    def to_json(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True)

    @classmethod
    def compute_hash(cls, event_dict: Dict[str, Any]) -> str:
        # Compute hash of the event without the global_chain_hash itself
        data = {k: v for k, v in event_dict.items() if k != "global_chain_hash"}
        encoded = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
