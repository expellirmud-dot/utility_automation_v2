class OptimizationSimulator:
    def simulate(self, pipeline, strategy):
        # Taking snapshot of original latency
        original_latency = pipeline.telemetry_snapshot(strategy["stage"])

        pipeline.apply_temp_change(strategy)
        
        # Taking snapshot of new simulated latency
        new_latency = pipeline.telemetry_snapshot(strategy["stage"])

        pipeline.rollback_temp_change()

        return {
            "before": original_latency,
            "after": new_latency,
            "improvement": original_latency - new_latency
        }
