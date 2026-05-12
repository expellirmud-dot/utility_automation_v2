from typing import Dict, Any, List
import hashlib
import json

class StateProjector:
    """
    Pure Function Projector: state = f(event_log)
    STRICTLY IDEMPOTENT: apply(event, state) + apply(event, state) = apply(event, state)
    """
    @staticmethod
    def project(event_log: List[Any]) -> Dict[str, Any]:
        state = {
            "active_policies": {},
            "trust_levels": {},
            "_last_epoch": -1,
            "_last_seq_id": -1,
            "_state_hash": None
        }
        
        # Sort events by seq_id to ensure deterministic replay
        sorted_events = sorted(event_log, key=lambda x: (x.epoch, x.seq_id))
        
        seen_positions = set()

        for event in sorted_events:
            # IDEMPOTENCY CHECK: Skip if event already processed
            event_position = (event.epoch, event.seq_id, event.event_id)
            if event_position in seen_positions:
                continue
            seen_positions.add(event_position)

            if event.type == "POLICY_UPDATE":
                payload = event.payload
                state["active_policies"][payload["rule_id"]] = payload["logic"]
            elif event.type == "AUTH_CHANGE":
                payload = event.payload
                state["trust_levels"][payload["identity_id"]] = payload["level"]

            state["_last_epoch"] = event.epoch
            state["_last_seq_id"] = event.seq_id
            
        state["_state_hash"] = StateValidator.compute_state_hash(state)
        return state

class StateValidator:
    @staticmethod
    def compute_state_hash(state: Dict[str, Any]) -> str:
        # Remove the hash itself before computing
        data = {k: v for k, v in state.items() if k != "_state_hash"}
        encoded = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
