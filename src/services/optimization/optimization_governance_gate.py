class OptimizationGovernanceGate:
    def approve(self, simulation_result):
        # Must have an improvement
        if simulation_result["improvement"] <= 0:
            return False
            
        # Optimization must be significant enough (e.g., > 0.2s)
        if simulation_result["improvement"] < 0.2:
            return False
            
        return True
