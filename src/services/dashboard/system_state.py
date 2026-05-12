class SystemStateAggregator:
    def build(self, telemetry, control_state, events):
        return {
            "health_score": telemetry.get("stability", 0),
            "latency_p95": telemetry.get("p95_latency", 0),
            "drift_level": telemetry.get("drift", 0),
            "accuracy": telemetry.get("accuracy", 0),
            "active_healings": len(events.get("healing", [])),
            "optimization_count": control_state.get("optimizations", 0)
        }
