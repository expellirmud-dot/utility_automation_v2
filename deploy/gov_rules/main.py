import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
from src.services.rules.default_rules import DEFAULT_RULES
from deploy.shared.auth import verify_service_token

app = FastAPI(title="gov-rules")

registry = RuleRegistry()
for rule in DEFAULT_RULES:
    registry.register(rule)

rule_engine = RuleEngine(registry)

class EvaluateRequest(BaseModel):
    role: str
    action: str
    system_state: str

@app.post("/evaluate", dependencies=[Depends(verify_service_token)])
async def evaluate_rules(req: EvaluateRequest):
    try:
        result = rule_engine.evaluate(
            role=req.role,
            action=req.action,
            system_state=req.system_state
        )
        return result
    except Exception as e:
        # Rule engine failure MUST fail closed (DENY)
        return {
            "decision": "DENY",
            "rule_id": "ENGINE_ERROR",
            "rule_name": f"Error: {str(e)}",
            "priority": 0
        }

@app.get("/health")
async def health():
    # gov-rules: rule registry loaded successfully
    if len(registry.all_rules()) > 0:
        return {"status": "healthy", "rules_count": len(registry.all_rules())}
    return {"status": "unhealthy", "reason": "No rules loaded"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
