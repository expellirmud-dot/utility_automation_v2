from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.services.audit.event_ledger import EventLedger
from src.services.audit.event_models import AuditEvent
from src.services.observability.metrics.metrics_registry import metrics
from src.services.observability.health.health_diagnostics import HealthDiagnostics
from src.services.observability.telemetry_middleware import observability_middleware
import os
import time

app = FastAPI(title="gov-audit")

app.middleware("http")(observability_middleware)

# Load from env
LEDGER_PATH = os.getenv("LEDGER_PATH", "ledger/events.log")
ledger = EventLedger(path=LEDGER_PATH)

class AuditEventRequest(BaseModel):
    event_type: str
    role: str
    action: str
    decision: str
    system_state: dict
    metadata: dict = {}

@app.get("/health")
async def health():
    status = HealthDiagnostics.get_status(ledger)
    return status

@app.get("/metrics")
async def get_metrics():
    return metrics.expose_metrics()

@app.post("/append")
async def append_event(req: AuditEventRequest):
    start = time.time()
    try:
        event = AuditEvent(
            event_type=req.event_type,
            role=req.role,
            action=req.action,
            decision=req.decision,
            system_state=req.system_state,
            metadata=req.metadata
        )
        ledger.append(event)
        
        # Record metric
        duration = (time.time() - start) * 1000
        metrics.audit_append_latency_ms.observe(duration)
        
        return {"status": "recorded", "event_id": event.event_id}
    except Exception as e:
        metrics.fail_closed_events_total.inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/replay")
async def replay_events():
    return ledger.replay()
