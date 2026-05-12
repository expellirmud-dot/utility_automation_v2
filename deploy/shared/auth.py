import os
import json
from fastapi import Header, HTTPException, status, Request
from .security.secret_provider import get_internal_service_token
from .security.request_signing import RequestSigner
from .security.replay_protection import nonce_registry

async def verify_service_token(
    request: Request,
    x_service_signature: str = Header(...),
    x_service_timestamp: str = Header(...),
    x_service_nonce: str = Header(...)
):
    secret = get_internal_service_token()
    signer = RequestSigner(secret)
    
    # Verify replay / expiration
    try:
        ts = float(x_service_timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp")
        
    if not nonce_registry.register_and_validate(x_service_nonce, ts):
        raise HTTPException(status_code=401, detail="Replay attack or expired request detected")
        
    # Get payload for signature
    body = await request.body()
    payload = body.decode() if body else ""
    
    # Reconstruct path and query
    path = request.url.path
    
    if not signer.verify_signature(x_service_signature, request.method, path, payload, x_service_timestamp, x_service_nonce):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )
    return True
