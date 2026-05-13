from __future__ import annotations

from fastapi.testclient import TestClient

from src.tests.certification.deterministic_certifier import DeterministicCertifier
from src.ui import ops_overview_api


client = TestClient(ops_overview_api.app)


def test_s6_system_health_adapter_and_federation_done_criteria():
    projections = client.get("/ops/api/projections")
    overview = client.get("/ops/api/overview")

    assert projections.status_code == 200
    assert overview.status_code == 200

    cards = projections.json()["cards"]
    assert len(cards) == 7

    keys = [card["key"] for card in cards]
    assert keys == [
        "incident_review",
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]

    for card in cards:
        assert card["status"] in {"connected", "degraded", "not_connected"}
        assert card["read_only"] is True
        assert card["authority_coupled"] is False

    system_health = {item["key"]: item for item in cards}["system_health"]
    assert system_health["source_type"] == "system_health_read_model"
    assert system_health["status"] in {"connected", "degraded"}


def test_s6_route_governance_compatibility_and_federation_only_routes():
    routes = client.get("/ops/api/route-governance")
    surfaces = client.get("/ops/api/surfaces")

    assert routes.status_code == 200
    assert routes.json()["valid"] is True

    assert surfaces.status_code == 200
    for surface in surfaces.json()["surfaces"]:
        assert surface["allowed_methods"] == ["GET"]


def test_s6_certifier_remains_full_score():
    result = DeterministicCertifier().run_all_certifications()
    assert result["overall_score"] == 100.0
