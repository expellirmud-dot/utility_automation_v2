class HealingIntentDetector:
    def detect(self, history):
        if history.get("recent_heal_count", 0) > 3:
            return "OVER_HEALING_RISK"

        if history.get("last_heal_failed", False):
            return "RECENT_FAILURE_RISK"

        return "NORMAL"
