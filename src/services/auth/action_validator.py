class ActionValidator:
    def __init__(self, auth_engine):
        self.auth = auth_engine

    def validate(self, role, action, system_state):
        # safety override rule (highest priority)
        if system_state == "CRITICAL" and action == "rollback":
            return "ALLOW"

        allowed = self.auth.is_allowed(role, action)

        if not allowed:
            return "DENY"

        return "ALLOW"
