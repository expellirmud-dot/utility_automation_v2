class BottleneckView:
    def analyze(self, bottlenecks):
        severity_map = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}

        return {
            "top_critical": sorted(
                bottlenecks,
                key=lambda x: severity_map.get(x.get("severity", "MEDIUM"), 0),
                reverse=True
            )[:5],

            "distribution": {
                "OCR": sum(1 for b in bottlenecks if b["stage"] == "OCR"),
                "SEMANTIC": sum(1 for b in bottlenecks if b["stage"] == "SEMANTIC"),
                "GOVERNANCE": sum(1 for b in bottlenecks if b["stage"] == "GOVERNANCE")
            }
        }
