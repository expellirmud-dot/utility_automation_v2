from pathlib import Path
import os

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.ui.read_only_route_governance import (
    ReadOnlyRouteGovernanceError,
    inspect_read_only_routes,
    validate_read_only_route_governance,
)
from src.ui.projection_federation import ProjectionFederationService, card_to_dict
from src.ui.read_only_surface_registry import list_ops_exposed_surfaces

router = APIRouter(prefix="/ops", tags=["Ops Overview"])

_UI_ROOT = Path(__file__).resolve().parents[2] / "ui"
validate_read_only_route_governance()
_federation_service = ProjectionFederationService.build_default()


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


class RouteGovernanceSummary(BaseModel):
    valid: bool
    checked_routes: int
    violations: int


class ProjectionProviderStatusEntry(BaseModel):
    key: str
    status: str
    label: str
    source_ref: str
    provider_kind: str
    connected: bool
    stale: bool


class ProjectionFederationCardEntry(BaseModel):
    key: str
    title: str
    domain: str
    status: str
    label: str
    provider_status: ProjectionProviderStatusEntry
    read_only: bool
    authority_coupled: bool
    source_type: str
    fallback_active: bool
    item_count: int
    stable_order: int


class ProjectionFederationResponse(BaseModel):
    cards: list[ProjectionFederationCardEntry]


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


class RouteGovernanceViolationEntry(BaseModel):
    path: str
    method: str
    reason: str


class RouteGovernanceResponse(BaseModel):
    valid: bool
    checked_routes: int
    registry_surface_count: int
    violations: list[RouteGovernanceViolationEntry]


def _strict_route_governance_enabled() -> bool:
    return os.getenv("OPS_ROUTE_GOVERNANCE_STRICT", "0") == "1"


def _build_route_governance_response() -> RouteGovernanceResponse:
    report = inspect_read_only_routes(app=app)
    return RouteGovernanceResponse(
        valid=report.valid,
        checked_routes=report.checked_routes,
        registry_surface_count=report.registry_surface_count,
        violations=[
            RouteGovernanceViolationEntry(path=item.path, method=item.method, reason=item.reason)
            for item in report.violations
        ],
    )

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
    report = _federation_service.report()
    cards = [
        OpsOverviewCard(
            key=card.key,
            title=card.title,
            projection_source=card.source_type,
            read_only=card.read_only,
            authority_coupled=card.authority_coupled,
            fallback_active=card.fallback_active,
            status=card.status,
            label=card.label,
        )
        for card in report.cards
    ]
    governance = _build_route_governance_response()
    cards.append(
        OpsOverviewCard(
            key="route_governance",
            title="Route Governance",
            projection_source="/ops/api/route-governance",
            read_only=True,
            authority_coupled=False,
            fallback_active=False,
            status="connected" if governance.valid else "not_connected",
            label=(
                f"valid | checked_routes={governance.checked_routes} | violations={len(governance.violations)}"
                if governance.valid
                else f"invalid | checked_routes={governance.checked_routes} | violations={len(governance.violations)}"
            ),
        )
    )
    return OpsOverviewResponse(cards=cards)




@router.get("/api/projections", response_model=ProjectionFederationResponse)
def get_projection_federation() -> ProjectionFederationResponse:
    report = _federation_service.report()
    return ProjectionFederationResponse(cards=[card_to_dict(item) for item in report.cards])

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


@router.get("/api/route-governance", response_model=RouteGovernanceResponse)
def get_route_governance() -> RouteGovernanceResponse:
    return _build_route_governance_response()


app = FastAPI(title="Ops Overview Console")
app.include_router(router)

if _strict_route_governance_enabled():
    strict_report = inspect_read_only_routes(app=app)
    if not strict_report.valid:
        raise ReadOnlyRouteGovernanceError(
            "OPS_ROUTE_GOVERNANCE_STRICT=1 and route governance is invalid: "
            f"checked_routes={strict_report.checked_routes}, violations={len(strict_report.violations)}"
        )
