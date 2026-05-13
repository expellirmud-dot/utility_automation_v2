from types import SimpleNamespace


class SecureControlPlane:
    def __init__(self, gateway, control_plane):
        self.gateway = gateway
        self.control_plane = control_plane

    def request_action(self, role, action, system_state):
        trusted_context = (
            role
            if hasattr(role, "trusted") and hasattr(role, "role")
            else SimpleNamespace(trusted=True, role=role, identity_id=str(role))
        )
        decision = self.gateway.execute(trusted_context, action, system_state)

        if decision != "ACTION_ALLOWED":
            return decision

        # Assuming control_plane exposes methods by action name
        return getattr(self.control_plane, action, lambda: {"status": "NOT_FOUND"})()
