class StabilityScorer:
    def score(self, metrics):
        score = (
            metrics["accuracy"] * 0.5 +
            (1 - metrics["latency"]) * 0.2 +
            (1 - metrics["drift"]) * 0.3
        )
        return score
