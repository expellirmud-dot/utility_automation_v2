from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse

from .incident_review_models import IncidentReviewListResponse
from .incident_review_service import IncidentReviewService
from .projection_providers import JsonSnapshotProjectionProvider, LiveIncidentReviewProjectionProvider

router = APIRouter(prefix="/incident-review", tags=["Incident Review"])
_snapshot_provider = JsonSnapshotProjectionProvider(Path(__file__).with_name("projection_snapshot.json"))
service = IncidentReviewService(
    provider=LiveIncidentReviewProjectionProvider(
        incident_provider=_snapshot_provider,
        replay_provider=_snapshot_provider,
        mesh_provider=_snapshot_provider,
        policy_provider=_snapshot_provider,
        lineage_provider=_snapshot_provider,
    )
)

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
