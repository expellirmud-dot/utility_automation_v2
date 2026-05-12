class OptimizationStrategyGenerator:
    def generate(self, bottlenecks):
        strategies = []
        for b in bottlenecks:
            if b["stage"] == "OCR":
                strategies.append({
                    "stage": "OCR",
                    "action": "reduce_image_resolution",
                    "impact": "HIGH_SPEED_GAIN",
                    "risk": "LOW"
                })
            elif b["stage"] == "SEMANTIC":
                strategies.append({
                    "stage": "SEMANTIC",
                    "action": "enable_rule_cache",
                    "impact": "MEDIUM_SPEED_GAIN",
                    "risk": "LOW"
                })
            elif b["stage"] == "FINANCIAL":
                strategies.append({
                    "stage": "FINANCIAL",
                    "action": "remove_redundant_validation",
                    "impact": "HIGH_SPEED_GAIN",
                    "risk": "MEDIUM"
                })
        return strategies
