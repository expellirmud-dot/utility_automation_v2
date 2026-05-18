from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import FastAPI
from fastapi.routing import APIRoute

from src.ui.read_only_surface_registry import ReadOnlySurfaceEntry, list_read_only_surfaces

_FORBIDDEN_ROUTE_PREFIXES = (
    "/control",
    "/control_ops",
    "/ops/control",
    "/api/control",
)
_FORBIDDEN_ACTION_LABELS = ("approve", "reject", "retry", "execute", "repair", "promote")
_ALLOWED_READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}

_EXPLICIT_BOUNDED_MUTATION_ROUTES = {
    "/ops/api/runtime-tasks/create": {"POST"},
    "/ops/api/runtime-tasks/start": {"POST"},
    "/ops/api/runtime-tasks/finish": {"POST"},
}


@dataclass(frozen=True)
class RouteGovernanceViolation:
    path: str
    method: str
    reason: str


@dataclass(frozen=True)
class RouteGovernanceReport:
    valid: bool
    checked_routes: int
    registry_surface_count: int
    violations: tuple[RouteGovernanceViolation, ...]


class ReadOnlyRouteGovernanceError(ValueError):
    pass


def validate_read_only_route_governance(
    surfaces: tuple[ReadOnlySurfaceEntry, ...] | None = None,
) -> tuple[ReadOnlySurfaceEntry, ...]:
    surface_list = surfaces if surfaces is not None else list_read_only_surfaces()

    for surface in surface_list:
        if tuple(surface.allowed_methods) != ("GET",):
            raise ReadOnlyRouteGovernanceError(f"{surface.key} allows non-GET methods")
        if not surface.read_only:
            raise ReadOnlyRouteGovernanceError(f"{surface.key} is not read-only")
        if surface.authority_coupled:
            raise ReadOnlyRouteGovernanceError(f"{surface.key} must not be authority coupled")

        lowered_fields = (
            surface.key.lower(),
            surface.title.lower(),
            surface.route_prefix.lower(),
            surface.api_prefix.lower(),
        )
        for label in _FORBIDDEN_ACTION_LABELS:
            if any(label in value for value in lowered_fields):
                raise ReadOnlyRouteGovernanceError(f"{surface.key} contains forbidden action label: {label}")

        if surface.exposed_in_ops:
            for forbidden in _FORBIDDEN_ROUTE_PREFIXES:
                if surface.route_prefix.startswith(forbidden) or surface.api_prefix.startswith(forbidden):
                    raise ReadOnlyRouteGovernanceError(
                        f"{surface.key} exposes forbidden route prefix {forbidden}"
                    )

    return tuple(surface_list)


def inspect_read_only_routes(
    app: FastAPI | None = None,
    routes: Iterable[APIRoute] | None = None,
    surfaces: tuple[ReadOnlySurfaceEntry, ...] | None = None,
) -> RouteGovernanceReport:
    surface_list = validate_read_only_route_governance(surfaces)
    exposed_prefixes = tuple(item.route_prefix.lower() for item in surface_list if item.exposed_in_ops)
    route_list = tuple(routes if routes is not None else (app.routes if app is not None else ()))

    violations: list[RouteGovernanceViolation] = []
    checked_routes = 0

    for route in route_list:
        if not isinstance(route, APIRoute):
            continue

        path = route.path
        lowered_path = path.lower()
        if not any(lowered_path.startswith(prefix) for prefix in exposed_prefixes):
            continue

        checked_routes += 1
        methods = tuple(sorted(route.methods or {"GET"}))
        for method in methods:
            lowered_method = method.lower()
            if method.upper() not in _ALLOWED_READ_ONLY_METHODS:
                if not (path in _EXPLICIT_BOUNDED_MUTATION_ROUTES and method.upper() in _EXPLICIT_BOUNDED_MUTATION_ROUTES[path]):
                    violations.append(
                        RouteGovernanceViolation(path=path, method=method, reason="non_read_only_method")
                    )

            if any(lowered_path.startswith(prefix) for prefix in _FORBIDDEN_ROUTE_PREFIXES):
                violations.append(
                    RouteGovernanceViolation(path=path, method=method, reason="forbidden_control_prefix")
                )

            if any(action in lowered_path or action in lowered_method for action in _FORBIDDEN_ACTION_LABELS):
                violations.append(
                    RouteGovernanceViolation(path=path, method=method, reason="forbidden_action_keyword")
                )

    stable_violations = tuple(sorted(violations, key=lambda item: (item.path, item.method, item.reason)))
    return RouteGovernanceReport(
        valid=not stable_violations,
        checked_routes=checked_routes,
        registry_surface_count=len(surface_list),
        violations=stable_violations,
    )
