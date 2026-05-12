import hmac
import hashlib
import time
import uuid

class RequestSigner:
    def __init__(self, secret: str):
        self.secret = secret.encode()

    def generate_signature(self, method: str, path: str, payload: str, timestamp: str, nonce: str) -> str:
        """Generates an HMAC signature for the request."""
        msg = f"{method}:{path}:{payload}:{timestamp}:{nonce}".encode()
        return hmac.new(self.secret, msg, hashlib.sha256).hexdigest()
        
    def sign_request_headers(self, method: str, path: str, payload: str = "") -> dict:
        timestamp = str(time.time())
        nonce = uuid.uuid4().hex
        sig = self.generate_signature(method, path, payload, timestamp, nonce)
        
        return {
            "X-Service-Timestamp": timestamp,
            "X-Service-Nonce": nonce,
            "X-Service-Signature": sig
        }

    def verify_signature(self, signature: str, method: str, path: str, payload: str, timestamp: str, nonce: str) -> bool:
        expected = self.generate_signature(method, path, payload, timestamp, nonce)
        return hmac.compare_digest(expected, signature)
