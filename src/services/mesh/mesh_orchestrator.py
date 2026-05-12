from typing import List, Dict, Any
from src.services.mesh.mesh_nodes import LeaderNode, WorkerNode, MeshNode
from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.mesh.sync_manager import SyncManager

class QuorumGate:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold

    def validate_approval(self, approval_bundle: Dict[str, Any]) -> bool:
        #- Approval object: {"event_id": "...", "approvers": ["nodeA", "nodeB"], "signatures": [...]}
        approvers = approval_bundle.get("approvers", [])
        if len(approvers) >= self.threshold:
            return True
        return False

class MeshOrchestrator:
    def __init__(self):
        self.leader = LeaderNode("leader-01")
        self.workers = [WorkerNode(f"worker-{i}", public_key=self.leader.public_key) for i in range(3)]
        self.quorum = QuorumGate(threshold=2)

    def submit_critical_event(self, actor: str, event_type: str, payload: Dict[str, Any], signatures: List[str]):
        # 1. Quorum check
        if not self.quorum.validate_approval({"approvers": signatures}):
            raise Exception("Quorum not reached for critical event")
            
        # 2. Leader commits
        event = self.leader.propose_event(actor, event_type, payload, "SIGNED_BY_QUORUM")
        
        # 3. Broadcast to workers
        for worker in self.workers:
            result = worker.apply_event(event)
            if result in ("RECONCILED", "FORK_DETECTED"):
                SyncManager.perform_anti_entropy_sync(worker, self.leader)
            
        return event
