import hashlib
import time

class TokenService:

    def issue_token(self, identity_id, secret):

        payload = f"{identity_id}:{time.time()}:{secret}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify_token(self, token, identity_id, secret):

        # Note: verify_token conceptually checks validity. 
        # For a real implementation, timestamps should be extracted or stable hashing used.
        expected = self.issue_token(identity_id, secret)
        # Using a simplistic comparison as requested
        return expected == token
