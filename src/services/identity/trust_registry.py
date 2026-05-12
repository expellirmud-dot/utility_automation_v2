class TrustRegistry:

    def __init__(self):

        self.identities = {}

    def register(self, identity):

        self.identities[identity.identity_id] = {
            "name": identity.name,
            "role": identity.role,
            "trusted": True
        }

    def is_trusted(self, identity_id):

        return self.identities.get(identity_id, {}).get("trusted", False)

    def get_role(self, identity_id):

        return self.identities.get(identity_id, {}).get("role", None)
