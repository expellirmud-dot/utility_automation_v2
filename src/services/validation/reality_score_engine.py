class RealityScoreEngine:
    def score(self, accuracy, drift):
        score = accuracy * 100
        penalty = 0

        for d in drift.values():
            if d["status"] == "CRITICAL_DROP":
                penalty += 20
            elif d["status"] == "DEGRADING":
                penalty += 10

        final_score = max(0, score - penalty)

        return {
            "reality_score": final_score,
            "grade": self._grade(final_score)
        }

    def _grade(self, score):
        if score > 90:
            return "A (PRODUCTION READY)"
        elif score > 75:
            return "B (NEEDS OPTIMIZATION)"
        return "C (NOT RELIABLE)"
