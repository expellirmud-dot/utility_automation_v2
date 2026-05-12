from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
import os

app = FastAPI(title="gov-rules")

# Initialize services
registry = RuleRegistry()
# In production, this would load from DB
engine = RuleEngine(registry)

class EvaluateRequest(BaseModel):
    role: str
    action: str
    system_state: dict

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gov-rules"}

@app.post("/evaluate")
async def evaluate_rules(req: EvaluateRequest):
    result = engine.evaluate(req.role, req.action, req.system_state)
    return result
