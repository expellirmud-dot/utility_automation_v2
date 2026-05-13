from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app
from src.ui.projection_federation import ProjectionFederationService


client = TestClient(app)


def test_federation_stable_order_and_read_only_contract():
    report = ProjectionFederationService.build_default().report()
    assert [card.key for card in report.cards] == [
        "incident_review",
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]
    assert [card.stable_order for card in report.cards] == [10, 20, 30, 40, 50, 60, 70]
    assert all(card.read_only is True for card in report.cards)
    assert all(card.authority_coupled is False for card in report.cards)


def test_incident_and_domain_providers_connected_deterministically():
    cards = ProjectionFederationService.build_default().report().cards
    by_key = {card.key: card for card in cards}

    assert by_key["incident_review"].status == "connected"
    assert by_key["incident_review"].source_type in {"runtime_projection", "file_projection"}

    expected = {
        "recovery": (2, "Connected", "connected", "recovery_projection"),
        "simulation": (1, "Connected", "connected", "simulation_projection"),
        "mesh": (3, "Connected", "connected", "mesh_projection"),
        "policy": (1, "Connected", "connected", "policy_projection"),
        "replay": (2, "Connected", "connected", "replay_projection"),
        "system_health": (1, "Connected", "connected", "system_health_telemetry"),
    }
    for key, (count, label, status, source_type) in expected.items():
        card = by_key[key]
        assert card.item_count == count
        assert card.label == label
        assert card.status == status
        assert card.source_type == source_type
        assert card.fallback_active is False


def test_ops_projections_get_only_and_shape():
    response = client.get('/ops/api/projections')
    assert response.status_code == 200
    payload = response.json()
    assert list(payload.keys()) == ["cards"]

    first = payload["cards"][0]
    assert list(first.keys()) == [
        "key",
        "title",
        "domain",
        "status",
        "label",
        "read_only",
        "authority_coupled",
        "source_type",
        "fallback_active",
        "item_count",
        "stable_order",
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/projections').status_code == 405
