from typing import List, Dict, Any
from src.services.mesh.mesh_nodes import LeaderNode, WorkerNode
from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.event_sourcing.projection.state_projector import StateProjector

class ReplayConsistencyChecker:
    @staticmethod
    def check(live_state: Dict[str, Any], event_log: List[CanonicalEvent]) -> bool:
        # Project the log from genesis
        replayed_state = StateProjector.project(event_log)
        
        # Compare root hashes
        return live_state.get("_state_hash") == replayed_state.get("_state_hash")
