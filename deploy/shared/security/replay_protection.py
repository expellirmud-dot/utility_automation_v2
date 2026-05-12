import time

class NonceRegistry:
    def __init__(self, expiration_seconds=60):
        self.nonces = {}
        self.expiration_seconds = expiration_seconds

    def register_and_validate(self, nonce: str, timestamp: float) -> bool:
        """
        Validates the nonce hasn't been seen recently and isn't expired.
        Returns True if valid, False if replay attack or expired.
        """
        current_time = time.time()
        
        # Check expiration (e.g. older than 60s)
        if current_time - timestamp > self.expiration_seconds:
            return False
            
        # Check if in future
        if timestamp > current_time + 5:
            return False
            
        # Clean up old nonces to prevent memory leak
        self._cleanup(current_time)
        
        if nonce in self.nonces:
            return False
            
        self.nonces[nonce] = current_time
        return True
        
    def _cleanup(self, current_time):
        keys_to_delete = [k for k, v in self.nonces.items() if current_time - v > self.expiration_seconds]
        for k in keys_to_delete:
            del self.nonces[k]

# Global instance for the service
nonce_registry = NonceRegistry()
