class RealityReport:
    def generate(self, accuracy, drift, score):
        return {
            "accuracy": accuracy,
            "drift_analysis": drift,
            "reality_score": score["reality_score"],
            "grade": score["grade"],
            "status": "VALIDATED" if score["reality_score"] > 80 else "FAILED"
        }
