import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.optimization.optimization_strategy_generator import OptimizationStrategyGenerator
from src.services.optimization.optimization_decision_engine import OptimizationDecisionEngine
from src.services.optimization.optimization_simulator import OptimizationSimulator
from src.services.optimization.optimization_governance_gate import OptimizationGovernanceGate
from src.services.optimization.auto_optimizer import AutoOptimizer

class MockBottleneckDetector:
    def get_latest(self):
        return [{"stage": "SEMANTIC", "severity": "HIGH", "avg_latency": 1.4}]

class MockPipeline:
    def __init__(self):
        self.temp_applied = False
        self.perm_applied = False

    def telemetry_snapshot(self, stage):
        if self.temp_applied:
            return 0.9  # simulated improvement
        return 1.4

    def apply_temp_change(self, strategy):
        self.temp_applied = True

    def rollback_temp_change(self):
        self.temp_applied = False

    def apply_permanent_change(self, strategy):
        self.perm_applied = True

def test_auto_optimizer():
    detector = MockBottleneckDetector()
    generator = OptimizationStrategyGenerator()
    selector = OptimizationDecisionEngine()
    simulator = OptimizationSimulator()
    gate = OptimizationGovernanceGate()
    
    optimizer = AutoOptimizer(detector, generator, selector, simulator, gate)
    pipeline = MockPipeline()

    result = optimizer.optimize(pipeline)

    assert "status" in result
    assert result["status"] == "OPTIMIZED"
    assert result["strategy"]["stage"] == "SEMANTIC"
    assert result["improvement"] == pytest.approx(0.5)  # 1.4 - 0.9
    assert pipeline.perm_applied is True
    assert pipeline.temp_applied is False # Rolled back after sim

def test_auto_optimizer_rejected():
    detector = MockBottleneckDetector()
    generator = OptimizationStrategyGenerator()
    selector = OptimizationDecisionEngine()
    simulator = OptimizationSimulator()
    gate = OptimizationGovernanceGate()
    
    optimizer = AutoOptimizer(detector, generator, selector, simulator, gate)
    
    class MockBadPipeline(MockPipeline):
        def telemetry_snapshot(self, stage):
            if self.temp_applied:
                return 1.3 # Only 0.1 improvement, governance gate requires >= 0.2
            return 1.4
            
    bad_pipeline = MockBadPipeline()

    result = optimizer.optimize(bad_pipeline)

    assert result["status"] == "REJECTED_BY_GOVERNANCE"
    assert bad_pipeline.perm_applied is False
