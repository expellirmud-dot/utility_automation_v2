import os

class SecretProvider:
    def __init__(self):
        self._secrets = {}
        
    def get_secret(self, secret_name: str, default: str = None) -> str:
        """
        Fetch a secret, checking docker secrets first, then environment.
        """
        # Support Docker secrets via /run/secrets
        secret_file_path = f"/run/secrets/{secret_name}"
        if os.path.exists(secret_file_path):
            with open(secret_file_path, 'r') as f:
                return f.read().strip()
                
        # Fallback to environment variable
        env_val = os.getenv(secret_name.upper())
        if env_val:
            return env_val
            
        return default

# Global instance
secrets = SecretProvider()

def get_internal_service_token() -> str:
    token = secrets.get_secret("internal_service_token")
    if not token:
        raise RuntimeError("INTERNAL_SERVICE_TOKEN is missing. System insecure.")
    return token
