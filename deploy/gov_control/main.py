import os
import sys
import httpx
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from deploy.shared.auth import verify_service_token
from src.services.consensus.causal_ledger import CausalClosureLedger
from src.services.consensus.causal_validator import CausalClosureValidator
from src.services.consensus.quorum_engine import QuorumEngine
from src.services.consensus.finalizer_kernel import FinalizerKernel
from src.services.consensus.state_projector import StateProjector
from src.services.consensus.sync_engine import SyncEngine
from src.services.consensus.cdml_runtime import CDMLRuntime, ProposalEngine

app = FastAPI(title="gov-control-cdml")

# Bootstrapping CDML Runtime
node_id = os.getenv("NODE_ID", "node-1")
ledger = CausalClosureLedger()
validator = CausalClosureValidator()
quorum = QuorumEngine(node_id=node_id, validator_registry={node_id}) # Self-quorum for standalone wiring
finalizer = FinalizerKernel(ledger.event_store)
projector = StateProjector(ledger.event_store)
sync = SyncEngine(ledger.event_store)
proposal = ProposalEngine(node_id)

cdml = CDMLRuntime(ledger, validator, quorum, finalizer, projector, sync, proposal)

class ExecuteRequest(BaseModel):
    identity_id: str
    action: str
    system_state: str

def mock_apply_fn(state: dict, event):
    # Pure deterministic reducer
    new_state = state.copy()
    action = event.payload.get("action")
    if action:
        new_state["actions_executed"] = new_state.get("actions_executed", 0) + 1
        new_state["last_action"] = action
    return new_state

@app.post("/execute", dependencies=[Depends(verify_service_token)])
async def execute(cmd: ExecuteRequest):
    """CDML Control Plane Write Path"""
    # Write is Always Event
    result = await cdml.handle_command(cmd.dict())
    if result["status"] != "OK":
        raise HTTPException(status_code=400, detail=result)
    return result

@app.get("/state")
def get_state():
    """CDML Control Plane Read Path (Single Truth Source)"""
    return cdml.query_state({"status": "initialized"}, mock_apply_fn)

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "cdml-native"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
