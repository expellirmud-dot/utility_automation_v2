from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse

from .incident_review_models import IncidentReviewListResponse
from .incident_review_service import IncidentReviewService, MockIncidentReviewProvider

router = APIRouter(prefix="/incident-review", tags=["Incident Review"])
service = IncidentReviewService(provider=MockIncidentReviewProvider())

_UI_ROOT = Path(__file__).resolve().parents[3] / "ui"


@router.get("/api/incidents", response_model=IncidentReviewListResponse)
def get_incidents() -> IncidentReviewListResponse:
    return IncidentReviewListResponse(incidents=service.list_incidents())


@router.get("", response_class=FileResponse)
def get_console() -> FileResponse:
    return FileResponse(_UI_ROOT / "incident_review.html")


@router.get("/incident_review.css", response_class=FileResponse)
def get_console_css() -> FileResponse:
    return FileResponse(_UI_ROOT / "incident_review.css")


@router.get("/incident_review.js", response_class=FileResponse)
def get_console_js() -> FileResponse:
    return FileResponse(_UI_ROOT / "incident_review.js")


app = FastAPI(title="Incident Review Console")
app.include_router(router)
