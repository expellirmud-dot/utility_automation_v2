from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ReadOnlySurfaceEntry:
    key: str
    title: str
    route_prefix: str
    api_prefix: str
    allowed_methods: tuple[str, ...]
    status: str
    authority_coupled: bool
    read_only: bool
    exposed_in_ops: bool
    stable_order: int


_READ_ONLY_SURFACES: Final[tuple[ReadOnlySurfaceEntry, ...]] = (
    ReadOnlySurfaceEntry(
        key="ops_console",
        title="Ops Console",
        route_prefix="/ops",
        api_prefix="/ops/api",
        allowed_methods=("GET",),
        status="connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=True,
        stable_order=10,
    ),
    ReadOnlySurfaceEntry(
        key="incident_review",
        title="Incident Review",
        route_prefix="/incident-review",
        api_prefix="/incident-review/api",
        allowed_methods=("GET",),
        status="connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=True,
        stable_order=20,
    ),
    ReadOnlySurfaceEntry(
        key="recovery_dashboard",
        title="Recovery Dashboard",
        route_prefix="/recovery-dashboard",
        api_prefix="/recovery-dashboard/api",
        allowed_methods=("GET",),
        status="not_connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=False,
        stable_order=30,
    ),
    ReadOnlySurfaceEntry(
        key="simulation_dashboard",
        title="Simulation Dashboard",
        route_prefix="/simulation-dashboard",
        api_prefix="/simulation-dashboard/api",
        allowed_methods=("GET",),
        status="not_connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=False,
        stable_order=40,
    ),
    ReadOnlySurfaceEntry(
        key="telemetry_dashboard",
        title="Telemetry Dashboard",
        route_prefix="/telemetry-dashboard",
        api_prefix="/telemetry-dashboard/api",
        allowed_methods=("GET",),
        status="not_connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=False,
        stable_order=50,
    ),
    ReadOnlySurfaceEntry(
        key="runtime_console",
        title="Runtime Console",
        route_prefix="/runtime-console",
        api_prefix="/ops/api/runtime-tasks",
        allowed_methods=("GET",),
        status="connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=True,
        stable_order=60,
    ),
)


def list_read_only_surfaces() -> tuple[ReadOnlySurfaceEntry, ...]:
    return tuple(sorted(_READ_ONLY_SURFACES, key=lambda item: item.stable_order))


def list_ops_exposed_surfaces() -> tuple[ReadOnlySurfaceEntry, ...]:
    return tuple(item for item in list_read_only_surfaces() if item.exposed_in_ops)
