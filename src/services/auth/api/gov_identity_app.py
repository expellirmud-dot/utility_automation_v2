from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.services.identity.resolver import IdentityResolver
from src.services.identity.trust_registry import TrustRegistry
from src.services.identity.token_service import TokenService
import os

app = FastAPI(title="gov-identity")

# Initialize services
trust_registry = TrustRegistry()
token_service = TokenService()
resolver = IdentityResolver(trust_registry, token_service)

class ResolveRequest(BaseModel):
    identity_id: str
    token: str
    secret: str

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gov-identity"}

@app.post("/resolve")
async def resolve_identity(req: ResolveRequest):
    result = resolver.resolve(req.identity_id, req.token, req.secret)
    if not result:
        raise HTTPException(status_code=401, detail="Identity resolution failed")
    return result
