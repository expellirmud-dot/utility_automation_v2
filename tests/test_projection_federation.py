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
        "fallback_reason",
        "item_count",
        "stable_order",
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/projections').status_code == 405


class _OkProvider:
    def read_metadata(self):
        class _Meta:
            status = "connected"
            label = "Connected"
            source_type = "ok_source"
            fallback_active = False
            item_count = 7

        return _Meta()


class _FailProvider:
    def read_metadata(self):
        raise RuntimeError("sensitive provider internals")


def test_one_provider_failure_is_isolated_and_endpoint_stays_200(monkeypatch):
    original_builder = ProjectionFederationService.build_default

    def _build_faulty():
        service = original_builder()
        providers = dict(service._providers)
        providers["mesh"] = _FailProvider()
        providers["policy"] = _OkProvider()
        return ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    monkeypatch.setattr("src.ui.ops_overview_api.ProjectionFederationService.build_default", _build_faulty)

    from src.ui import ops_overview_api

    ops_overview_api._federation_service = _build_faulty()
    response = client.get('/ops/api/projections')

    assert response.status_code == 200
    cards = {item["key"]: item for item in response.json()["cards"]}
    assert cards["mesh"]["status"] == "degraded"
    assert cards["mesh"]["fallback_active"] is True
    assert cards["policy"]["status"] == "connected"
    assert cards["policy"]["item_count"] == 7


def test_fallback_payload_is_deterministic_for_same_failure():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["simulation"] = _FailProvider()
    unstable = ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    first = {c.key: c for c in unstable.report().cards}["simulation"]
    second = {c.key: c for c in unstable.report().cards}["simulation"]

    assert first == second
    assert first.fallback_reason == "provider_exception"


def test_failure_status_is_truthful_degraded_or_not_connected():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["replay"] = _FailProvider()
    unstable = ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    failing_card = {c.key: c for c in unstable.report().cards}["replay"]
    assert failing_card.status in {"degraded", "not_connected"}
