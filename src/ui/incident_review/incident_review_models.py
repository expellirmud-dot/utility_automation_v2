from pydantic import BaseModel


class IncidentReviewItem(BaseModel):
    incident_id: str
    title: str
    severity: str
    status: str
    summary: str
    operator_note: str


class IncidentReviewListResponse(BaseModel):
    incidents: list[IncidentReviewItem]
