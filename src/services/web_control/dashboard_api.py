class WebDashboardAPI:
    def __init__(self, control_plane):
        self.control_plane = control_plane

    def get_state(self):
        # Maps to the control plane's state builder or state aggregator
        return getattr(self.control_plane, "get_state", lambda: {"status": "UNKNOWN"})()

    def override_decision(self, decision_id, action):
        # Override a decision manually via human-in-loop
        return getattr(self.control_plane, "override", lambda d, a: {"status": "OVERRIDDEN", "id": d, "action": a})(decision_id, action)

    def adjust_threshold(self, value):
        # Change a systemic threshold (e.g., latency limits or confidence bounds)
        return getattr(self.control_plane, "set_threshold", lambda v: {"status": "THRESHOLD_UPDATED", "value": v})(value)
