from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app
from src.ui.projection_federation import ProjectionFederationService
from src.ui.projection_federation_providers import FederationReadMetadata


client = TestClient(app)


class _ExplodingProvider:
    def read_metadata(self) -> FederationReadMetadata:
        raise RuntimeError("provider down")


def _is_truthful_deterministic_degraded(card) -> bool:
    return (
        card.status in {"degraded", "not_connected"}
        and card.fallback_active is True
        and card.source_type == "deterministic_fallback"
        and "deterministic fallback" in card.label.lower()
    )


def test_projection_federation_contracts_all_domains():
    report = ProjectionFederationService.build_default().report()

    expected_keys = [
        "incident_review",
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]
    assert [card.key for card in report.cards] == expected_keys
    assert [card.stable_order for card in report.cards] == [10, 20, 30, 40, 50, 60, 70]
    assert all(card.read_only is True for card in report.cards)
    assert all(card.authority_coupled is False for card in report.cards)

    for card in report.cards:
        assert card.status in {"connected", "degraded", "not_connected"}
        assert card.status == "connected" or _is_truthful_deterministic_degraded(card)


def test_provider_isolation_uses_deterministic_fallback_on_exception():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["policy"] = _ExplodingProvider()
    isolated = ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    by_key = {card.key: card for card in isolated.report().cards}
    assert by_key["policy"].status == "degraded"
    assert by_key["policy"].fallback_active is True
    assert by_key["policy"].source_type == "deterministic_fallback"
    assert "Deterministic fallback" in by_key["policy"].label
    assert by_key["recovery"].status == "connected"


def test_truthful_status_and_get_only_routes_are_preserved():
    overview = client.get("/ops/api/overview")
    projections = client.get("/ops/api/projections")
    assert overview.status_code == 200
    assert projections.status_code == 200

    projection_cards = projections.json()["cards"]
    assert len(projection_cards) == 7
    for card in projection_cards:
        assert card["status"] in {"connected", "degraded", "not_connected"}
        if card["status"] != "connected":
            assert card["fallback_active"] is True
            assert card["source_type"] == "deterministic_fallback"

    for route in ["/ops/api/overview", "/ops/api/projections"]:
        for method in ["post", "put", "patch", "delete"]:
            assert getattr(client, method)(route).status_code == 405


def test_import_guard_for_federation_modules():
    forbidden_tokens = [
        "mesh_orchestrator",
        "control_ops",
        "execution",
        "mutation",
    ]
    modules = [
        Path("src/ui/projection_federation.py"),
        Path("src/ui/projection_federation_providers.py"),
    ]

    imported_names: set[str] = set()
    for module in modules:
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                imported_names.add(base)
                imported_names.update(f"{base}.{alias.name}" for alias in node.names)

    joined = "\n".join(sorted(imported_names)).lower()
    for forbidden in forbidden_tokens:
        assert forbidden not in joined
