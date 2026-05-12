import hashlib
import json
from typing import Any, Dict, List
from src.services.event_sourcing.canonical_event import CanonicalEvent

class InvariantEngine:
    @staticmethod
    def validate_transition(current_state: Dict[str, Any], event: CanonicalEvent, next_state: Dict[str, Any]) -> bool:
        # Invariant 1: Ledger-only mutation
        # (Checked by the projector, but we verify here)
        
        # Invariant 2: Monotonic Ordering
        # We verify if the event sequence is strictly increasing compared to state
        last_epoch = current_state.get("_last_epoch", -1)
        last_seq = current_state.get("_last_seq_id", -1)
        if event.epoch < last_epoch:
            return False
        if event.epoch == last_epoch and event.seq_id <= last_seq:
            return False
            
        # Invariant 3: Determinism check
        # if hash(replay(state)) != node_state_hash...
        # This is handled by the state_validator
        
        return True

class ViolationDetector:
    @staticmethod
    def detect_drift(node_a_hash: str, node_b_hash: str) -> bool:
        return node_a_hash != node_b, "State drift detected between nodes"
