import json
import os
from src.services.mesh.mesh_orchestrator import MeshOrchestrator
from src.tests.certification.replay_consistency_checker import ReplayConsistencyChecker
from src.tests.certification.fork_resolution_tester import ForkResolutionTester
from src.tests.certification.quorum_integrity_tester import QuorumIntegrityTester
from src.tests.certification.convergence_validator import ConvergenceValidator
from src.tests.certification.adversarial_fault_injector import AdversarialFaultInjector
from src.services.event_sourcing.projection.state_projector import StateProjector

class DeterministicCertifier:
    def __init__(self):
        self.orch = MeshOrchestrator()
        self.results = {}

    def run_all_certifications(self):
        print("Starting Deterministic Mesh Certification...")
        
        # 1. Ledger Integrity & Deterministic Replay
        # Process a few events first
        self.orch.submit_critical_event("admin", "INIT", {"val": 1}, ["n1", "n2"])
        self.orch.submit_critical_event("admin", "INIT", {"val": 2}, ["n1", "n2"])
        
        # Test replay on workers
        replay_pass = True
        for worker in self.orch.workers:
            if not ReplayConsistencyChecker.check(worker.current_state, worker.event_log):
                replay_pass = False
                break
        self.results["determinism"] = "PASS" if replay_pass else "FAIL"

        idempotent_pass = True
        for worker in self.orch.workers:
            replayed_once = StateProjector.project(worker.event_log)
            replayed_twice = StateProjector.project(worker.event_log + worker.event_log)
            if replayed_once.get("_state_hash") != replayed_twice.get("_state_hash"):
                idempotent_pass = False
                break
        self.results["idempotent_replay"] = "PASS" if idempotent_pass else "FAIL"
        
        # 2. Fork Safety
        self.results["fork_safety"] = "PASS" if ForkResolutionTester.test_fork_safety(self.orch) else "FAIL"
        
        # 3. Quorum Integrity
        self.results["quorum_integrity"] = "PASS" if QuorumIntegrityTester.test_quorum_threshold(self.orch) else "FAIL"
        
        # 4. Convergence Guarantee
        conv_pass = ConvergenceValidator.validate_all_nodes_converged(self.orch.workers + [self.orch.leader])
        self.results["convergence"] = "PASS" if conv_pass else "FAIL"

        anti_entropy_pass = ConvergenceValidator.test_recovery_convergence(self.orch.workers[0], self.orch.leader)
        self.results["anti_entropy_sync"] = "PASS" if anti_entropy_pass else "FAIL"
        
        # 5. Byzantine Resilience
        byz_pass = True
        for worker in self.orch.workers:
            try:
                # Try to inject forged event
                forged = AdversarialFaultInjector.create_forged_event(self.orch.leader.event_log[-1])
                worker.apply_event(forged)
                # If it was applied, it's a failure because forgers should be rejected
                byz_pass = False
                break
            except Exception:
                pass # Correctly rejected
        self.results["byzantine_resilience"] = "PASS" if byz_pass else "FAIL"
        
        # Overall Score
        passed = sum(1 for v in self.results.values() if v == "PASS")
        self.results["overall_score"] = (passed / len(self.results)) * 100
        
        # Export report
        os.makedirs("output/certification", exist_ok=True)
        with open("output/certification/cert_report.json", "w") as f:
            json.dump(self.results, f, indent=4)
            
        return self.results

if __name__ == "__main__":
    certifier = DeterministicCertifier()
    print(certifier.run_all_certifications())
