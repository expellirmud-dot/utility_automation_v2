import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.identity.resolver import IdentityResolver
from src.services.identity.trust_registry import TrustRegistry
from src.services.identity.token_service import TokenService
from src.services.identity.models import ActorIdentity
from deploy.shared.auth import verify_service_token

app = FastAPI(title="gov-identity")

registry = TrustRegistry()
token_service = TokenService()
resolver = IdentityResolver(registry, token_service)

class ResolveRequest(BaseModel):
    identity_id: str
    token: str
    secret: str

class RegisterRequest(BaseModel):
    name: str
    role: str

@app.post("/register", dependencies=[Depends(verify_service_token)])
async def register_identity(req: RegisterRequest):
    identity = ActorIdentity(name=req.name, role=req.role)
    registry.register(identity)
    return {"identity_id": identity.identity_id, "name": identity.name, "role": identity.role}

@app.post("/resolve", dependencies=[Depends(verify_service_token)])
async def resolve_identity(req: ResolveRequest):
    result = resolver.resolve(req.identity_id, req.token, req.secret)
    if not result:
        raise HTTPException(status_code=403, detail="Identity not trusted or token invalid")
    return result

@app.get("/health")
async def health():
    # gov-identity: token validation operational
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
