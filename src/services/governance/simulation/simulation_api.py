from typing import List
from fastapi import APIRouter, HTTPException
from src.services.governance.simulation.simulation_request_models import SimulationRequest, SimulationResponse
import hashlib
import json
import time

router = APIRouter(prefix="/simulation", tags=["Simulation"])

# Simulated storage for reports (Immutable cache)
_simulation_reports = {}

def _compute_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@router.post("/simulate_policy_change_request", response_model=SimulationResponse)
async def simulate_policy_change_request(req: SimulationRequest):
    # Rule engine evaluation without writing to ledger
    simulation_hash = _compute_hash(req.model_dump())
    
    report = {
        "simulation_hash": simulation_hash,
        "impact": {"status": "simulated", "affected_rules": [req.policy_id]},
        "manual_review_required": True,
        "warnings": ["Simulated policy change deviates from current ledger state"]
    }
    
    _simulation_reports[simulation_hash] = report
    return report

@router.post("/simulate_scenarios_request")
async def simulate_scenarios_request(scenarios: List[SimulationRequest]):
    # Batch processing
    return [_compute_hash(s.model_dump()) for s in scenarios]

@router.get("/reports/{report_hash}")
async def get_simulation_report(report_hash: str):
    if report_hash not in _simulation_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    return _simulation_reports[report_hash]

@router.get("/recent")
async def list_recent_simulation_reports():
    return list(_simulation_reports.keys())
