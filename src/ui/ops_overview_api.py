from pathlib import Path
import os
import json

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
    fallback_reason: str
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


class OpsDomainPanelResponse(BaseModel):
    domain: str
    status: str
    source: str
    items: list[dict[str, object]]


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


def _read_snapshot_items(snapshot_name: str, *, source: str) -> OpsDomainPanelResponse:
    snapshot_path = Path(__file__).resolve().parent / snapshot_name
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        raw_items = payload.get("items", []) if isinstance(payload, dict) else []
        normalized_items = raw_items if isinstance(raw_items, list) else []
        normalized_items = sorted(
            [item for item in normalized_items if isinstance(item, dict)],
            key=lambda item: str(item.get("id", "")),
        )
        status = "connected" if normalized_items else "empty"
        return OpsDomainPanelResponse(
            domain=source,
            status=status,
            source=source,
            items=normalized_items,
        )
    except (OSError, ValueError, TypeError, AttributeError):
        return OpsDomainPanelResponse(
            domain=source,
            status="degraded",
            source="deterministic_fallback",
            items=[],
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


@router.get("/api/recovery", response_model=OpsDomainPanelResponse)
def get_recovery_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("recovery_projection_snapshot.json", source="recovery")


@router.get("/api/simulation", response_model=OpsDomainPanelResponse)
def get_simulation_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("simulation_projection_snapshot.json", source="simulation")


@router.get("/api/mesh", response_model=OpsDomainPanelResponse)
def get_mesh_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("mesh_projection_snapshot.json", source="mesh")


@router.get("/api/policy", response_model=OpsDomainPanelResponse)
def get_policy_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("policy_projection_snapshot.json", source="policy")


@router.get("/api/replay", response_model=OpsDomainPanelResponse)
def get_replay_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("replay_projection_snapshot.json", source="replay")


@router.get("/api/system-health", response_model=OpsDomainPanelResponse)
def get_system_health_panel() -> OpsDomainPanelResponse:
    return _read_snapshot_items("system_health_telemetry_snapshot.json", source="system_health")


app = FastAPI(title="Ops Overview Console")
app.include_router(router)

if _strict_route_governance_enabled():
    strict_report = inspect_read_only_routes(app=app)
    if not strict_report.valid:
        raise ReadOnlyRouteGovernanceError(
            "OPS_ROUTE_GOVERNANCE_STRICT=1 and route governance is invalid: "
            f"checked_routes={strict_report.checked_routes}, violations={len(strict_report.violations)}"
        )
