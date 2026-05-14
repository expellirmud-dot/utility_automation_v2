from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from src.services.dashboard.projection_api import router as dashboard_projection_router
from src.services.ops_console.api import router as ops_domain_panel_router

app = FastAPI(title="gov-control")
app.include_router(dashboard_projection_router)
app.include_router(ops_domain_panel_router)

# Service URLs from env
IDENTITY_URL = os.getenv("IDENTITY_URL", "http://gov-identity:8002")
RULES_URL = os.getenv("RULES_URL", "http://gov-rules:8003")
AUDIT_URL = os.getenv("AUDIT_URL", "http://gov-audit:8001")

@app.get("/health")
async def health():
    # Check downstream dependencies
    async with httpx.AsyncClient() as client:
        try:
            # Simple check for other services
            await client.get(f"{IDENTITY_URL}/health")
            await client.get(f"{RULES_URL}/health")
            await client.get(f"{AUDIT_URL}/health")
            return {"status": "healthy", "downstreams": "reachable"}
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}

@app.post("/execute")
async def execute_governance(payload: dict):
    # Simplified Orchestration matching ProductionPipeline logic
    # In reality, this would call the services in sequence
    return {"status": "orchestrated", "result": "deterministic_success"}
