class BottleneckDriftDetector:
    def detect(self, baseline, current):
        drift_report = {}

        for stage in current:
            if stage not in baseline:
                continue

            drift = current[stage]["p95"] - baseline[stage]["p95"]

            drift_report[stage] = {
                "drift": drift,
                "status": self._classify(drift)
            }

        return drift_report

    def _classify(self, drift):
        if drift > 1.0:
            return "CRITICAL"
        elif drift > 0.5:
            return "HIGH"
        return "STABLE"
