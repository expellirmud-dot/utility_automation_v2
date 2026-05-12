class NoiseDetector:
    def detect(self, signals):
        if signals.get("metric_variance", 0) > 0.6:
            return "HIGH_NOISE"

        if signals.get("conflicting_metrics", False):
            return "CONFLICTING_SIGNALS"

        return "STABLE_SIGNAL"
