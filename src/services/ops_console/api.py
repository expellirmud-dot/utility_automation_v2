from __future__ import annotations

from typing import Callable

from fastapi import APIRouter

from src.services.ops_console.db_projection_reader import OpsProjectionReader
from src.services.ops_console.formatters import (
    format_mesh_panel,
    format_policy_panel,
    format_recovery_panel,
    format_replay_panel,
    format_simulation_panel,
    format_system_health_panel,
)
from src.services.ops_console.models import DomainPanelData


router = APIRouter(prefix="/ops/api", tags=["Ops Domain Panels"])
reader = OpsProjectionReader()


@router.get("/recovery")
async def get_recovery_panel() -> dict:
    return _panel_response("recovery", format_recovery_panel)


@router.get("/simulation")
async def get_simulation_panel() -> dict:
    return _panel_response("simulation", format_simulation_panel)


@router.get("/mesh")
async def get_mesh_panel() -> dict:
    return _panel_response("mesh", format_mesh_panel)


@router.get("/policy")
async def get_policy_panel() -> dict:
    return _panel_response("policy", format_policy_panel)


@router.get("/replay")
async def get_replay_panel() -> dict:
    return _panel_response("replay", format_replay_panel)


@router.get("/system-health")
async def get_system_health_panel() -> dict:
    return _panel_response("system_health", format_system_health_panel)


@router.get("/panels")
async def get_domain_panels() -> dict:
    panels = [
        _panel_response("recovery", format_recovery_panel),
        _panel_response("simulation", format_simulation_panel),
        _panel_response("mesh", format_mesh_panel),
        _panel_response("policy", format_policy_panel),
        _panel_response("replay", format_replay_panel),
        _panel_response("system_health", format_system_health_panel),
    ]
    return {
        "advisory_only": True,
        "panel_count": len(panels),
        "panels": panels,
        "metadata": {
            "source": "sqlite_projection",
            "projection_only": True,
            "ordering": "recovery, simulation, mesh, policy, replay, system_health",
        },
    }


def _panel_response(domain: str, formatter: Callable[[dict], DomainPanelData]) -> dict:
    panel = formatter(reader.read_domain(domain))
    if hasattr(panel, "model_dump"):
        return panel.model_dump()
    return panel.dict()
