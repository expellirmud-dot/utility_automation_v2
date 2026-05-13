from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from src.ui import ops_overview_api
from src.ui.projection_federation import ProjectionFederationService
from src.ui.projection_federation_providers import FederationReadMetadata


@dataclass(frozen=True)
class _IncidentMetadata:
    status_label: str = "Connected"
    source_type: str = "incident_review_projection"
    fallback_active: bool = False
    read_only: bool = True
    authority_coupled: bool = False


class _StubIncidentService:
    def source_metadata(self) -> _IncidentMetadata:
        return _IncidentMetadata()

    def list_incidents(self) -> list[dict[str, str]]:
        return [{"id": "INC-001"}]


class _Provider:
    def __init__(self, metadata: FederationReadMetadata | None = None, *, should_raise: bool = False) -> None:
        self._metadata = metadata
        self._should_raise = should_raise

    def read_metadata(self) -> FederationReadMetadata:
        if self._should_raise:
            raise RuntimeError("provider unavailable")
        assert self._metadata is not None
        return self._metadata


def _build_service_with_failures() -> ProjectionFederationService:
    providers = {
        "recovery": _Provider(
            FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type="recovery_projection",
                fallback_active=False,
                item_count=2,
            )
        ),
        "simulation": _Provider(
            FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type="simulation_projection",
                fallback_active=False,
                item_count=1,
            )
        ),
        "mesh": _Provider(should_raise=True),
        "policy": _Provider(
            FederationReadMetadata(
                label="Disconnected",
                status="not_connected",
                source_type="policy_projection",
                fallback_active=False,
                item_count=0,
            )
        ),
        "replay": _Provider(
            FederationReadMetadata(
                label="Degraded",
                status="degraded",
                source_type="replay_projection",
                fallback_active=True,
                item_count=0,
            )
        ),
        "system_health": _Provider(should_raise=True),
    }
    return ProjectionFederationService(incident_service=_StubIncidentService(), providers=providers)


def test_provider_exception_is_isolated_and_metadata_is_present(monkeypatch):
    monkeypatch.setattr(ops_overview_api, "_federation_service", _build_service_with_failures())
    client = TestClient(ops_overview_api.app)

    projections = client.get("/ops/api/projections")
    assert projections.status_code == 200

    cards = projections.json()["cards"]
    by_key = {card["key"]: card for card in cards}

    for key in ("mesh", "system_health"):
        card = by_key[key]
        assert card["status"] == "degraded"
        assert card["fallback_active"] is True
        assert card["provider_status"]["status"] == "degraded"
        assert card["provider_status"]["source_ref"] == "deterministic_fallback"

    for card in cards:
        provider_status = card["provider_status"]
        assert set(provider_status.keys()) == {
            "key",
            "status",
            "label",
            "source_ref",
            "provider_kind",
            "connected",
            "stale",
        }


def test_overview_still_works_when_providers_throw(monkeypatch):
    monkeypatch.setattr(ops_overview_api, "_federation_service", _build_service_with_failures())
    client = TestClient(ops_overview_api.app)

    overview = client.get("/ops/api/overview")
    assert overview.status_code == 200

    payload = overview.json()
    assert payload["cards"]
    keys = {item["key"] for item in payload["cards"]}
    assert "route_governance" in keys


def test_projection_federation_forbidden_import_guard():
    forbidden_import_prefixes = (
        "src.services.control_plane",
        "src.services.auth.control_gateway",
        "src.services.governance.policy_graph.promotion_pipeline",
        "src.services.event_sourcing.replay_engine",
    )

    file_path = Path("src/ui/projection_federation.py")
    module = ast.parse(file_path.read_text(encoding="utf-8"))

    imported_modules: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for name in node.names:
                imported_modules.add(name.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    for imported in imported_modules:
        assert not imported.startswith(forbidden_import_prefixes), imported


def test_ops_surfaces_are_get_only():
    client = TestClient(ops_overview_api.app)
    response = client.get("/ops/api/surfaces")
    assert response.status_code == 200
    for surface in response.json()["surfaces"]:
        assert surface["allowed_methods"] == ["GET"]
