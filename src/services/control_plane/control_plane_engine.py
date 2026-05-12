class ControlPlaneEngine:
    def decide(self, stability_score, intent, noise, budget):
        if noise == "HIGH_NOISE":
            return "BLOCK_HEALING"

        if intent == "OVER_HEALING_RISK":
            return "DELAY_HEALING"

        if not budget:
            return "BLOCK_HEALING"

        if stability_score > 0.85:
            return "BLOCK_HEALING"

        if stability_score < 0.6:
            return "ALLOW_HEALING"

        return "MONITOR_ONLY"
