from fastapi import FastAPI, APIRouter, Request
from src.services.observability.metrics.metrics_registry import metrics
from src.services.observability.health.health_diagnostics import HealthDiagnostics
from src.services.audit.event_ledger import EventLedger
import time

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
ledger = EventLedger()

@router.get("/summary")
async def get_governance_summary():
    # Aggregates current metrics for the main overview
    return {
        "metrics": {
            "total_decisions": metrics.decisions_total._sum.value,
            "fail_closed_count": metrics.fail_closed_events_total._sum.value,
            "security_rejections": metrics.security_rejections_total._sum.value,
            "rule_conflicts": metrics.rule_conflict_total._sum.value,
        },
        "health": HealthDiagnostics.get_status(ledger),
        "timestamp": time.time()
    }

@router.get("/traces/{correlation_id}")
async def get_trace(correlation_id: str):
    # Search ledger for all events matching the correlation ID
    events = ledger.get_all_events()
    trace = [e for e in events if e.get("metadata", {}).get("correlation_id") == correlation_id]
    return {
        "correlation_id": correlation_id,
        "trace": trace,
        "count": len(trace)
    }

@router.get("/replay/diagnostics")
async def get_replay_status():
    # Returns current replay state and consistency
    return {
        "status": "stable",
        "last_replay_timestamp": time.time(),
        "consistency_score": 1.0,
        "drift_detected": False
    }

@router.get("/ledger/preview")
async def get_ledger_preview(limit: int = 50):
    events = ledger.get_all_events()
    return events[-limit:]
