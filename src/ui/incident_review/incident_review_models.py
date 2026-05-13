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


class IncidentReviewSourceStatusResponse(BaseModel):
    source_type: str
    read_only: bool
    authority_coupled: bool
    fallback_active: bool
    source_ref: str
    status_label: str
