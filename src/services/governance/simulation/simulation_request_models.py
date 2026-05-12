from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class SimulationRequest(BaseModel):
    policy_id: str
    proposed_logic: Dict[str, Any]
    scenario_name: str

class ScenarioRequest(BaseModel):
    scenarios: List[SimulationRequest]

class SimulationResponse(BaseModel):
    simulation_hash: str
    impact: Dict[str, Any]
    manual_review_required: bool
    warnings: List[str]
