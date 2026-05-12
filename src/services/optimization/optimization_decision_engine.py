class OptimizationDecisionEngine:
    def select_best(self, strategies):
        # simple scoring model (can evolve to ML later)
        scored = []
        for s in strategies:
            score = 0
            
            if "HIGH_SPEED_GAIN" in s["impact"]:
                score += 3
            elif "MEDIUM_SPEED_GAIN" in s["impact"]:
                score += 2

            if s["risk"] == "LOW":
                score += 2
            elif s["risk"] == "MEDIUM":
                score += 1

            scored.append((score, s))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1] if scored else None
