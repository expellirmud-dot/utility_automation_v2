from src.services.auth.permissions import PERMISSIONS

class AuthEngine:
    def is_allowed(self, role, action):
        return PERMISSIONS.get(role, {}).get(action, False)
