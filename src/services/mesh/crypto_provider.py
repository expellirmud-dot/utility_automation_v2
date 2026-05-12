from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

class CryptoProvider:
    """
    Handles Ed25519 signing and verification for the Governance Mesh.
    """
    @staticmethod
    def generate_keypair():
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def sign(private_key, data: str) -> str:
        signature = private_key.sign(data.encode())
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify(public_key_bytes: bytes, data: str, signature: str) -> bool:
        try:
            if hasattr(public_key_bytes, "verify"):
                public_key = public_key_bytes
            else:
                public_key = serialization.load_pem_public_key(public_key_bytes)
            sig_bytes = base64.b64decode(signature)
            public_key.verify(sig_bytes, data.encode())
            return True
        except Exception:
            return False

    @staticmethod
    def serialize_public_key(public_key) -> bytes:
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
