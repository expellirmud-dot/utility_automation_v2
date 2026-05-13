from pathlib import Path
import os
import json
from dataclasses import dataclass

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
    item_count: int
    advisory_only: bool
    summaries: list[dict[str, object]]
    diagnostics: list[dict[str, object]]
    metadata: dict[str, object]
    items: list[dict[str, object]]


class RecoveryPanelResponse(OpsDomainPanelResponse):
    recovery_summaries: list[dict[str, object]]
    diagnoses: list[dict[str, object]]
    recovery_reports: list[dict[str, object]]
    recovery_classifications: list[dict[str, object]]
    advisory_plans_recent: list[dict[str, object]]


class SimulationPanelResponse(OpsDomainPanelResponse):
    scenario_summaries: list[dict[str, object]]
    advisory_outcomes: list[dict[str, object]]


class MeshPanelResponse(OpsDomainPanelResponse):
    node_summaries: list[dict[str, object]]
    convergence_state: dict[str, object]
    anti_entropy_health: dict[str, object]
    quorum_metadata: dict[str, object]
    topology_summaries: list[dict[str, object]]


class PolicyPanelResponse(OpsDomainPanelResponse):
    active_policy: dict[str, object]
    lineage: list[dict[str, object]]
    ancestry: list[dict[str, object]]
    rollback_metadata: dict[str, object]
    policy_health: dict[str, object]


class ReplayPanelResponse(OpsDomainPanelResponse):
    replay_certification: dict[str, object]
    determinism_verification: dict[str, object]
    replay_history_metadata: list[dict[str, object]]


class SystemHealthPanelResponse(OpsDomainPanelResponse):
    health_summaries: list[dict[str, object]]
    telemetry_rollups: list[dict[str, object]]
    diagnostics_rollup: list[dict[str, object]]
    degraded_indicators: list[dict[str, object]]
    provider_status: list[dict[str, object]]


@dataclass(frozen=True)
class DomainPanelConfig:
    source: str
    snapshot_name: str


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
            item_count=len(normalized_items),
            advisory_only=True,
            summaries=normalized_items,
            diagnostics=[],
            metadata={"deterministic_ordering": "id_asc", "snapshot": snapshot_name},
            items=normalized_items,
        )
    except (OSError, ValueError, TypeError, AttributeError):
        return OpsDomainPanelResponse(
            domain=source,
            status="degraded",
            source="deterministic_fallback",
            item_count=0,
            advisory_only=True,
            summaries=[],
            diagnostics=[{"code": "snapshot_unavailable", "domain": source}],
            metadata={"deterministic_ordering": "id_asc", "snapshot": snapshot_name},
            items=[],
        )


_DOMAIN_PANEL_CONFIG: dict[str, DomainPanelConfig] = {
    "recovery": DomainPanelConfig(source="recovery", snapshot_name="recovery_projection_snapshot.json"),
    "simulation": DomainPanelConfig(source="simulation", snapshot_name="simulation_projection_snapshot.json"),
    "mesh": DomainPanelConfig(source="mesh", snapshot_name="mesh_projection_snapshot.json"),
    "policy": DomainPanelConfig(source="policy", snapshot_name="policy_projection_snapshot.json"),
    "replay": DomainPanelConfig(source="replay", snapshot_name="replay_projection_snapshot.json"),
    "system_health": DomainPanelConfig(source="system_health", snapshot_name="system_health_telemetry_snapshot.json"),
}


def _read_domain_base(domain_key: str) -> OpsDomainPanelResponse:
    config = _DOMAIN_PANEL_CONFIG[domain_key]
    return _read_snapshot_items(config.snapshot_name, source=config.source)

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


@router.get("/api/recovery", response_model=RecoveryPanelResponse)
def get_recovery_panel() -> RecoveryPanelResponse:
    base = _read_domain_base("recovery")
    return RecoveryPanelResponse(
        **base.model_dump(),
        recovery_summaries=base.items,
        diagnoses=base.items,
        recovery_reports=base.items,
        recovery_classifications=base.items,
        advisory_plans_recent=base.items,
    )


@router.get("/api/simulation", response_model=SimulationPanelResponse)
def get_simulation_panel() -> SimulationPanelResponse:
    base = _read_domain_base("simulation")
    return SimulationPanelResponse(**base.model_dump(), scenario_summaries=base.items, advisory_outcomes=base.items)


@router.get("/api/mesh", response_model=MeshPanelResponse)
def get_mesh_panel() -> MeshPanelResponse:
    base = _read_domain_base("mesh")
    return MeshPanelResponse(
        **base.model_dump(),
        node_summaries=base.items,
        convergence_state={"status": base.status},
        anti_entropy_health={"status": base.status},
        quorum_metadata={"advisory_only": True},
        topology_summaries=base.items,
    )


@router.get("/api/policy", response_model=PolicyPanelResponse)
def get_policy_panel() -> PolicyPanelResponse:
    base = _read_domain_base("policy")
    return PolicyPanelResponse(
        **base.model_dump(),
        active_policy=base.items[0] if base.items else {},
        lineage=base.items,
        ancestry=base.items,
        rollback_metadata={"available": False, "advisory_only": True},
        policy_health={"status": base.status},
    )


@router.get("/api/replay", response_model=ReplayPanelResponse)
def get_replay_panel() -> ReplayPanelResponse:
    base = _read_domain_base("replay")
    return ReplayPanelResponse(
        **base.model_dump(),
        replay_certification={"status": base.status},
        determinism_verification={"ordering": "id_asc", "status": base.status},
        replay_history_metadata=base.items,
    )


@router.get("/api/system-health", response_model=SystemHealthPanelResponse)
def get_system_health_panel() -> SystemHealthPanelResponse:
    base = _read_domain_base("system_health")
    return SystemHealthPanelResponse(
        **base.model_dump(),
        health_summaries=base.items,
        telemetry_rollups=base.items,
        diagnostics_rollup=base.diagnostics,
        degraded_indicators=base.diagnostics,
        provider_status=base.items,
    )


app = FastAPI(title="Ops Overview Console")
app.include_router(router)

if _strict_route_governance_enabled():
    strict_report = inspect_read_only_routes(app=app)
    if not strict_report.valid:
        raise ReadOnlyRouteGovernanceError(
            "OPS_ROUTE_GOVERNANCE_STRICT=1 and route governance is invalid: "
            f"checked_routes={strict_report.checked_routes}, violations={len(strict_report.violations)}"
        )
