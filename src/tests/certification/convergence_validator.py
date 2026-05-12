from src.services.mesh.mesh_nodes import MeshNode
from src.services.mesh.sync_manager import SyncManager

class ConvergenceValidator:
    @staticmethod
    def validate_all_nodes_converged(nodes: list) -> bool:
        if not nodes:
            return True
            
        # Use first node as reference
        ref_hash = nodes[0].current_state.get("_state_hash")
        
        for node in nodes[1:]:
            if node.current_state.get("_state_hash") != ref_hash:
                return False
        return True

    @staticmethod
    def test_recovery_convergence(node: MeshNode, leader: MeshNode):
        # Simulate drift
        node.current_state["_state_hash"] = "CORRUPTED_HASH"
        
        # Trigger sync
        SyncManager.perform_anti_entropy_sync(node, leader)
        
        # Verify convergence
        return node.current_state.get("_state_hash") == leader.current_state.get("_state_hash")
