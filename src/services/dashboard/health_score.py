class SystemHealthScorer:
    def score(self, metrics):
        score = (
            metrics.get("accuracy", 0) * 0.4 +
            (1 - metrics.get("latency_p95", 0)) * 0.3 +
            (1 - metrics.get("drift_level", 0)) * 0.3
        )

        if score > 0.85:
            return ("STABLE", score)

        if score > 0.65:
            return ("DEGRADED", score)

        return ("CRITICAL", score)
