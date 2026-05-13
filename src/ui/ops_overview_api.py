from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.ui.incident_review.incident_review_service import IncidentReviewService
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory

router = APIRouter(prefix="/ops", tags=["Ops Overview"])

_UI_ROOT = Path(__file__).resolve().parents[2] / "ui"
_incident_service = IncidentReviewService(
    provider=IncidentReviewProviderFactory.build_live_default(
        Path(__file__).resolve().parent / "incident_review" / "projection_snapshot.json"
    )
)


class OpsOverviewCard(BaseModel):
    key: str
    title: str
    projection_source: str
    read_only: bool
    authority_coupled: bool
    fallback_active: bool
    status: str
    label: str


class OpsOverviewResponse(BaseModel):
    cards: list[OpsOverviewCard]


@router.get("", response_class=FileResponse)
def get_ops_console() -> FileResponse:
    return FileResponse(_UI_ROOT / "ops_console.html")


@router.get("/ops_console.css", response_class=FileResponse)
def get_ops_css() -> FileResponse:
    return FileResponse(_UI_ROOT / "ops_console.css")


@router.get("/ops_console.js", response_class=FileResponse)
def get_ops_js() -> FileResponse:
    return FileResponse(_UI_ROOT / "ops_console.js")


@router.get("/api/overview", response_model=OpsOverviewResponse)
def get_overview() -> OpsOverviewResponse:
    incident_metadata = _incident_service.source_metadata()
    cards = [
        OpsOverviewCard(
            key="incident_review",
            title="Incident Review",
            projection_source=incident_metadata.source_ref,
            read_only=incident_metadata.read_only,
            authority_coupled=incident_metadata.authority_coupled,
            fallback_active=incident_metadata.fallback_active,
            status="connected",
            label=incident_metadata.status_label,
        ),
        OpsOverviewCard(
            key="recovery_dashboard",
            title="Recovery Dashboard",
            projection_source="not_connected",
            read_only=True,
            authority_coupled=False,
            fallback_active=True,
            status="not_connected",
            label="Not connected",
        ),
        OpsOverviewCard(
            key="simulation_dashboard",
            title="Simulation Dashboard",
            projection_source="not_connected",
            read_only=True,
            authority_coupled=False,
            fallback_active=True,
            status="not_connected",
            label="Not connected",
        ),
        OpsOverviewCard(
            key="certifier_determinism",
            title="Certifier / Determinism",
            projection_source="not_connected",
            read_only=True,
            authority_coupled=False,
            fallback_active=True,
            status="not_connected",
            label="Not connected",
        ),
    ]
    return OpsOverviewResponse(cards=cards)


app = FastAPI(title="Ops Overview Console")
app.include_router(router)
