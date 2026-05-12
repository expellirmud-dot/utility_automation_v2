class TrustedContext:

    def __init__(self, identity_payload):

        self.identity_id = identity_payload["identity_id"]
        self.role = identity_payload["role"]
        self.trusted = identity_payload["trusted"]
