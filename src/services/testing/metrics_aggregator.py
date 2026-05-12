class MetricsAggregator:
    @staticmethod
    def aggregate(results: list) -> dict:
        total = len(results)
        passed = sum(1 for r in results if r["comparison"]["exact_match"])
        return {
            "total_bills": total,
            "success_rate": (passed / total) if total > 0 else 0
        }
