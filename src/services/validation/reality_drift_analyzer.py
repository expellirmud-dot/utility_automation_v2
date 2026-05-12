class RealityDriftAnalyzer:
    def analyze(self, simulation_metrics, real_metrics):
        drift_report = {}

        for key in real_metrics:
            sim = simulation_metrics.get(key, {}).get("accuracy", 0)
            real = real_metrics.get(key, {}).get("accuracy", 0)

            drift = real - sim
            drift_report[key] = {
                "drift": drift,
                "status": self._status(drift)
            }

        return drift_report

    def _status(self, drift):
        if drift < -0.1:
            return "CRITICAL_DROP"
        elif drift < -0.05:
            return "DEGRADING"
        return "STABLE"
