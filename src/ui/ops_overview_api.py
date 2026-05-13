from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.ui.incident_review.incident_review_service import IncidentReviewService
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory
from src.ui.read_only_route_governance import validate_read_only_route_governance
from src.ui.read_only_surface_registry import list_ops_exposed_surfaces, list_read_only_surfaces

router = APIRouter(prefix="/ops", tags=["Ops Overview"])

_UI_ROOT = Path(__file__).resolve().parents[2] / "ui"
_incident_service = IncidentReviewService(
    provider=IncidentReviewProviderFactory.build_live_default(
        Path(__file__).resolve().parent / "incident_review" / "projection_snapshot.json"
    )
)
validate_read_only_route_governance()


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


class OpsSurfaceEntry(BaseModel):
    key: str
    title: str
    route_prefix: str
    api_prefix: str
    allowed_methods: list[str]
    status: str
    authority_coupled: bool
    read_only: bool
    exposed_in_ops: bool
    stable_order: int


class OpsSurfaceResponse(BaseModel):
    surfaces: list[OpsSurfaceEntry]


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
    cards: list[OpsOverviewCard] = []
    for surface in list_read_only_surfaces():
        if surface.key == "incident_review":
            cards.append(
                OpsOverviewCard(
                    key=surface.key,
                    title=surface.title,
                    projection_source=incident_metadata.source_ref,
                    read_only=incident_metadata.read_only,
                    authority_coupled=incident_metadata.authority_coupled,
                    fallback_active=incident_metadata.fallback_active,
                    status="connected",
                    label=incident_metadata.status_label,
                )
            )
            continue
        cards.append(
            OpsOverviewCard(
                key=surface.key,
                title=surface.title,
                projection_source="not_connected",
                read_only=surface.read_only,
                authority_coupled=surface.authority_coupled,
                fallback_active=True,
                status=surface.status,
                label="Not connected" if surface.status == "not_connected" else surface.status,
            )
        )
    return OpsOverviewResponse(cards=cards)


@router.get("/api/surfaces", response_model=OpsSurfaceResponse)
def get_ops_surfaces() -> OpsSurfaceResponse:
    surfaces = [
        OpsSurfaceEntry(
            key=surface.key,
            title=surface.title,
            route_prefix=surface.route_prefix,
            api_prefix=surface.api_prefix,
            allowed_methods=list(surface.allowed_methods),
            status=surface.status,
            authority_coupled=surface.authority_coupled,
            read_only=surface.read_only,
            exposed_in_ops=surface.exposed_in_ops,
            stable_order=surface.stable_order,
        )
        for surface in list_ops_exposed_surfaces()
    ]
    return OpsSurfaceResponse(surfaces=surfaces)


app = FastAPI(title="Ops Overview Console")
app.include_router(router)
