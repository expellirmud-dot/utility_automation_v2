import unittest
import os
import sys
import time
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from deploy.shared.security.request_signing import RequestSigner
from deploy.shared.security.replay_protection import NonceRegistry
from deploy.shared.security.secret_provider import SecretProvider

class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret-123"
        self.signer = RequestSigner(self.secret)
        self.nonce_registry = NonceRegistry(expiration_seconds=2)

    def test_forged_request_rejection(self):
        """Prove that a request signed with a different secret is rejected."""
        attacker_signer = RequestSigner("hacker-secret-999")
        
        method = "POST"
        path = "/evaluate"
        payload = '{"role": "admin"}'
        timestamp = str(time.time())
        nonce = uuid.uuid4().hex
        
        # Attacker signs the payload
        forged_sig = attacker_signer.generate_signature(method, path, payload, timestamp, nonce)
        
        # Target verifies with valid secret
        is_valid = self.signer.verify_signature(forged_sig, method, path, payload, timestamp, nonce)
        
        self.assertFalse(is_valid, "Forged request should be rejected")

    def test_replay_attack_prevention(self):
        """Prove that intercepting a valid request and resending it fails due to nonce tracking."""
        method = "POST"
        path = "/log"
        payload = '{"action": "rollback"}'
        timestamp = str(time.time())
        nonce = uuid.uuid4().hex
        
        # Valid signature generated
        sig = self.signer.generate_signature(method, path, payload, timestamp, nonce)
        self.assertTrue(self.signer.verify_signature(sig, method, path, payload, timestamp, nonce))
        
        # First request comes in
        is_first_valid = self.nonce_registry.register_and_validate(nonce, float(timestamp))
        self.assertTrue(is_first_valid, "First legitimate request should succeed")
        
        # Hacker intercepts and replays exactly the same headers
        is_replay_valid = self.nonce_registry.register_and_validate(nonce, float(timestamp))
        self.assertFalse(is_replay_valid, "Replayed request should be rejected")

    def test_expired_request_rejection(self):
        """Prove that a request delayed beyond expiration is rejected."""
        old_timestamp = time.time() - 10 # 10 seconds ago
        nonce = uuid.uuid4().hex
        
        is_valid = self.nonce_registry.register_and_validate(nonce, old_timestamp)
        self.assertFalse(is_valid, "Expired request should be rejected")
        
    def test_future_request_rejection(self):
        """Prove that a request with timestamp too far in the future is rejected."""
        future_timestamp = time.time() + 10 # 10 seconds in future
        nonce = uuid.uuid4().hex
        
        is_valid = self.nonce_registry.register_and_validate(nonce, future_timestamp)
        self.assertFalse(is_valid, "Future request should be rejected")

if __name__ == "__main__":
    unittest.main()
