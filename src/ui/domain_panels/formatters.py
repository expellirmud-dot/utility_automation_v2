from __future__ import annotations

from typing import Any
import json

from src.projections.db_projection_reader import ProjectionReadResult


PANEL_TITLES = {
    "recovery": "Recovery",
    "simulation": "Simulation",
    "mesh": "Mesh",
    "policy": "Policy",
    "replay": "Replay",
    "system_health": "System Health",
}

STABLE_ITEM_KEYS = (
    "stable_order",
    "epoch",
    "seq_id",
    "sequence",
    "id",
    "key",
    "event_hash",
    "hash",
    "artifact_hash",
    "domain",
)


def format_recovery_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("recovery", projection)


def format_simulation_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("simulation", projection)


def format_mesh_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("mesh", projection)


def format_policy_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("policy", projection)


def format_replay_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("replay", projection)


def format_system_health_panel(projection: ProjectionReadResult) -> dict[str, Any]:
    return _format_panel("system_health", projection)


def _format_panel(expected_domain: str, projection: ProjectionReadResult) -> dict[str, Any]:
    items = tuple(sorted((dict(item) for item in projection.items), key=_item_sort_key))
    diagnostics = dict(sorted(projection.diagnostics.items()))
    metadata = dict(sorted(projection.metadata.items()))
    metadata["domain"] = expected_domain
    metadata["title"] = PANEL_TITLES[expected_domain]

    return {
        "domain": expected_domain,
        "status": projection.status,
        "source": projection.source,
        "items": list(items),
        "advisory_only": True,
        "item_count": len(items),
        "summaries": _summaries(items),
        "diagnostics": diagnostics,
        "metadata": metadata,
    }


def _summaries(items: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        label = item.get("summary") or item.get("label") or item.get("title") or item.get("id") or item.get("key")
        summaries.append(
            {
                "stable_order": index,
                "id": str(item.get("id") or item.get("key") or item.get("event_hash") or index),
                "label": str(label or "projection_item"),
            }
        )
    return summaries


def _item_sort_key(item: dict[str, Any]) -> tuple[str, ...]:
    stable_values = tuple(str(item.get(key, "")) for key in STABLE_ITEM_KEYS)
    canonical = json.dumps(item, sort_keys=True, separators=(",", ":"), default=str)
    return (*stable_values, canonical)
