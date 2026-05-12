import numpy as np

class StatisticalAnalyzer:
    def analyze(self, telemetry_stats):
        report = {}

        for stage, stats in telemetry_stats.items():
            times = stats.get("samples", [])

            if not times:
                continue

            report[stage] = {
                "avg": float(np.mean(times)),
                "p50": float(np.percentile(times, 50)),
                "p95": float(np.percentile(times, 95)),
                "p99": float(np.percentile(times, 99)),
                "std_dev": float(np.std(times))
            }

        return report
