from src.services.mesh.mesh_orchestrator import MeshOrchestrator
from src.services.event_sourcing.canonical_event import CanonicalEvent

class QuorumIntegrityTester:
    @staticmethod
    def test_quorum_threshold(orch: MeshOrchestrator):
        # Test 1: Below threshold (should fail)
        try:
            orch.submit_critical_event(
                actor="admin", 
                event_type="CRITICAL_POLICY", 
                payload={"rule": "X"}, 
                signatures=["node1"] # Only 1 signature, threshold is 2
            )
            return False # Should have raised exception
        except Exception:
            pass # Correct behavior
            
        # Test 2: At threshold (should pass)
        try:
            orch.submit_critical_event(
                actor="admin", 
                event_type="CRITICAL_POLICY", 
                payload={"rule": "Y"}, 
                signatures=["node1", "node2"] # 2 signatures
            )
            return True
        except Exception:
            return False
