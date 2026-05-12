import os
import sys
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.audit.audit_logger import AuditLogger
from src.services.audit.replay_engine import ReplayEngine
from deploy.shared.auth import verify_service_token

app = FastAPI(title="gov-audit")

# Harden storage to SQLite
LEDGER_PATH = os.getenv("LEDGER_PATH", "ledger/events.db")
audit_logger = AuditLogger(ledger_path=LEDGER_PATH)
# ReplayEngine might need update to read from SQLite
replay_engine = ReplayEngine(log_path=LEDGER_PATH)

class AuditLogRequest(BaseModel):
    event_type: str
    role: str
    action: str
    decision: str
    system_state: str
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None

@app.post("/log", dependencies=[Depends(verify_service_token)])
async def log_event(req: AuditLogRequest, x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")):
    try:
        # Use key from payload or header
        key = req.idempotency_key or x_idempotency_key
        
        event_id = audit_logger.log(
            event_type=req.event_type,
            role=req.role,
            action=req.action,
            decision=req.decision,
            system_state=req.system_state,
            metadata=req.metadata,
            idempotency_key=key
        )
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        # Audit service failure MUST block governance actions
        raise HTTPException(status_code=500, detail=f"Ledger append failure: {str(e)}")

@app.get("/replay", dependencies=[Depends(verify_service_token)])
async def replay_events(action: Optional[str] = None):
    try:
        # Replay should now use the database
        events = audit_logger.ledger.replay()
        if action:
            events = [e for e in events if e['action'] == action]
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    try:
        # Check if DB is accessible
        audit_logger.ledger.get_all_events()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
