class BottleneckDetector:
    def detect(self, telemetry_stats):
        sorted_stages = sorted(
            telemetry_stats.items(),
            key=lambda x: x[1]["avg"],
            reverse=True
        )

        bottlenecks = []

        for stage, stats in sorted_stages:
            if stats["avg"] > 0.5:  # threshold
                bottlenecks.append({
                    "stage": stage,
                    "severity": self._classify(stats["avg"]),
                    "avg_latency": stats["avg"]
                })

        return bottlenecks

    def _classify(self, latency):
        if latency > 2:
            return "CRITICAL"
        elif latency > 1:
            return "HIGH"
        return "MEDIUM"
