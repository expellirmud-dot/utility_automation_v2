from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse

from .incident_review_models import IncidentReviewListResponse, IncidentReviewSourceStatusResponse
from .incident_review_service import IncidentReviewService
from .projection_providers import IncidentReviewProviderFactory

router = APIRouter(prefix="/incident-review", tags=["Incident Review"])
service = IncidentReviewService(
    provider=IncidentReviewProviderFactory.build_live_default(Path(__file__).with_name("projection_snapshot.json"))
)

_UI_ROOT = Path(__file__).resolve().parents[3] / "ui"


@router.get("/api/incidents", response_model=IncidentReviewListResponse)
def get_incidents() -> IncidentReviewListResponse:
    return IncidentReviewListResponse(incidents=service.list_incidents())




@router.get("/api/source-status", response_model=IncidentReviewSourceStatusResponse)
def get_source_status() -> IncidentReviewSourceStatusResponse:
    metadata = service.source_metadata()
    return IncidentReviewSourceStatusResponse(
        source_type=metadata.source_type,
        read_only=metadata.read_only,
        authority_coupled=metadata.authority_coupled,
        fallback_active=metadata.fallback_active,
        source_path=metadata.source_path,
        status_label=metadata.status_label,
    )


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
