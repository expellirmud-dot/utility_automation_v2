class IdentityResolver:

    def __init__(self, trust_registry, token_service):

        self.trust_registry = trust_registry
        self.token_service = token_service

    def resolve(self, identity_id, token, secret):

        # 1. verify identity exists
        if not self.trust_registry.is_trusted(identity_id):
            return None

        # 2. verify token authenticity
        valid = self.token_service.verify_token(token, identity_id, secret)

        if not valid:
            return None

        # 3. return trusted role
        role = self.trust_registry.get_role(identity_id)

        return {
            "identity_id": identity_id,
            "role": role,
            "trusted": True
        }
