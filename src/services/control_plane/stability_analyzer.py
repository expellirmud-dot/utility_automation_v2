class StabilityAnalyzer:
    def analyze(self, metrics):
        return {
            "accuracy": metrics.get("accuracy", 0),
            "latency": metrics.get("latency", 0),
            "drift": metrics.get("drift", 0),
            "volatility": metrics.get("volatility", 0)
        }
