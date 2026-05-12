class PerformanceReport:
    def generate(self, telemetry_stats, bottlenecks, causes):
        return {
            "summary": {
                "total_stages": len(telemetry_stats),
                "bottleneck_count": len(bottlenecks)
            },
            "bottlenecks": bottlenecks,
            "root_causes": causes,
            "recommendation": self._recommend(bottlenecks)
        }

    def _recommend(self, bottlenecks):
        if any(b["severity"] == "CRITICAL" for b in bottlenecks):
            return "OPTIMIZE CRITICAL PATH IMMEDIATELY"
        return "SYSTEM ACCEPTABLE BUT CAN BE OPTIMIZED"
