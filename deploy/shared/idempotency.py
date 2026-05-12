import hashlib
import json
from fastapi import Header, HTTPException, Request

def generate_request_fingerprint(identity_id: str, action: str, system_state: str, payload: dict = None) -> str:
    """
    Generates a deterministic fingerprint for a request.
    """
    content = {
        "identity_id": identity_id,
        "action": action,
        "system_state": system_state,
        "payload": payload or {}
    }
    dump = json.dumps(content, sort_keys=True)
    return hashlib.sha256(dump.encode()).hexdigest()

async def get_idempotency_key(
    x_request_id: str = Header(None, alias="X-Request-ID"),
    x_idempotency_key: str = Header(None, alias="X-Idempotency-Key")
) -> str:
    """
    Extracts the idempotency key from headers.
    Prioritizes X-Idempotency-Key then X-Request-ID.
    """
    key = x_idempotency_key or x_request_id
    if not key:
        # For gov-control, we might require one of these for critical actions
        return None
    return key
