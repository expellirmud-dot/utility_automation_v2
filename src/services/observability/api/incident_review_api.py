from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.services.observability.incident_review.provider import MockIncidentReviewProvider
from src.services.observability.incident_review.service import IncidentReviewService

router = APIRouter(prefix="/api/incident-review", tags=["incident-review"])
service = IncidentReviewService(provider=MockIncidentReviewProvider())


@router.get("/incidents")
def get_incidents() -> dict:
    return {"incidents": service.get_incidents()}


@router.get("/incidents/analytics")
def get_incident_analytics() -> dict:
    return service.get_analytics()


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    incident = service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
