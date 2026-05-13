from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.ui import ops_overview_api


client = TestClient(ops_overview_api.app)


def test_mesh_policy_replay_adapters_connected_and_read_only_flags():
    response = client.get("/ops/api/projections")
    assert response.status_code == 200

    cards = {item["key"]: item for item in response.json()["cards"]}
    for key, source_type in (
        ("mesh", "mesh_read_model"),
        ("policy", "policy_read_model"),
        ("replay", "replay_read_model"),
    ):
        card = cards[key]
        assert card["status"] in {"connected", "degraded"}
        assert card["source_type"] == source_type
        assert card["read_only"] is True
        assert card["authority_coupled"] is False


def test_mesh_policy_replay_degrade_truthfully_when_unavailable(tmp_path, monkeypatch):
    broken_base = tmp_path / "ui"
    broken_base.mkdir()

    from src.ui.projection_federation import ProjectionFederationService

    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)

    from src.ui.projection_federation_providers import ProjectionFederationProviderFactory

    broken = ProjectionFederationProviderFactory.build_defaults(broken_base)
    providers["mesh"] = broken["mesh"]
    providers["policy"] = broken["policy"]
    providers["replay"] = broken["replay"]

    monkeypatch.setattr(
        ops_overview_api,
        "_federation_service",
        ProjectionFederationService(incident_service=service._incident_service, providers=providers),
    )

    response = client.get("/ops/api/projections")
    assert response.status_code == 200
    cards = {item["key"]: item for item in response.json()["cards"]}

    for key in ("mesh", "policy", "replay"):
        card = cards[key]
        assert card["status"] == "degraded"
        assert card["provider_status"]["connected"] is False
        assert card["fallback_active"] is True
        assert card["item_count"] == 0


def test_s5_stable_ordering_unchanged_and_forbidden_import_guards():
    response = client.get("/ops/api/projections")
    assert response.status_code == 200
    assert [item["key"] for item in response.json()["cards"]] == [
        "incident_review",
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]

    module = ast.parse(Path("src/ui/projection_federation_providers.py").read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    forbidden = (
        "src.services.governance.policy_graph.promotion_pipeline",
        "src.services.event_sourcing.replay_engine",
        "src.services.control_plane",
        "src.services.governance.mesh",
    )
    for imported in imports:
        assert not imported.startswith(forbidden), imported
