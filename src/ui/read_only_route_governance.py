from __future__ import annotations

from src.ui.read_only_surface_registry import ReadOnlySurfaceEntry, list_read_only_surfaces

_FORBIDDEN_ROUTE_PREFIXES = (
    "/control_ops",
    "/ops/control",
    "/ops/api/control",
    "/ops/api/mutation",
)
_FORBIDDEN_ACTION_LABELS = ("approve", "reject", "retry", "execute", "repair", "promote")


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
