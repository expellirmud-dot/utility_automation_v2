class ProductionReport:
    def generate(self, stats, drift, results):
        return {
            "load_summary": {
                "total_requests": len(results)
            },
            "performance": stats,
            "drift_analysis": drift,
            "status": self._status(drift)
        }

    def _status(self, drift):
        if any(v["status"] == "CRITICAL" for v in drift.values()):
            return "SYSTEM_DEGRADED"

        return "STABLE"
