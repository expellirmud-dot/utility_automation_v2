class SafetyRules:
    def check(self, action, system_state):
        if system_state == "CRITICAL":
            if action in ["adjust_threshold", "override_decision"]:
                return "ESCALATE"

        return "OK"
