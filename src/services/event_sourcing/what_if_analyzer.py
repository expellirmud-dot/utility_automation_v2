class WhatIfAnalyzer:
    def analyze(self, simulation_result: dict):
        diff = simulation_result["diff"]
        risk_score = len(diff["changed_fields"]) * 0.1

        return {
            "risk_score": risk_score,
            "impact_level": self._classify(risk_score)
        }

    def _classify(self, risk):
        if risk < 0.1:
            return "LOW"
        elif risk < 0.3:
            return "MEDIUM"
        return "HIGH"
