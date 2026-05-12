from src.services.mesh.mesh_nodes import LeaderNode, WorkerNode
from src.services.mesh.mesh_orchestrator import MeshOrchestrator
from src.tests.certification.adversarial_fault_injector import AdversarialFaultInjector
from src.tests.certification.replay_consistency_checker import ReplayConsistencyChecker

class ForkResolutionTester:
    @staticmethod
    def test_fork_safety(orch: MeshOrchestrator):
        # Create a divergence
        leader = orch.leader
        worker = orch.workers[0]
        
        # Normal event
        e1 = leader.propose_event("admin", "POLICY_UPDATE", {"rule_id": "R1", "logic": "ALLOW"}, "sig")
        worker.apply_event(e1)
        
        # Inject a competing event directly to worker (Fork)
        forged = AdversarialFaultInjector.create_forged_event(e1)
        
        # Worker should either reject it or resolve it via canonical rules
        try:
            worker.apply_event(forged)
        except Exception:
            pass # Expected behavior if invariant engine blocks it
            
        # Final state must match leader
        return worker.current_state["_state_hash"] == leader.current_state["_state_hash"]
