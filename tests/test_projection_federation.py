from dataclasses import dataclass

from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app
from src.ui.projection_federation import ProjectionFederationService
from src.ui.projection_federation_providers import FederationReadMetadata


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

    incident_card = by_key["incident_review"]
    assert incident_card.source_type in {"runtime_projection", "file_projection"}
    expected_connected = not incident_card.fallback_active
    expected_status = "connected" if expected_connected else "not_connected"
    assert incident_card.status == expected_status
    assert incident_card.provider_status.connected is expected_connected
    assert incident_card.provider_status.source_ref == "projection_snapshot.json"

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
        assert card.provider_status.source_ref == source_type
        assert card.provider_status.connected is True
        assert card.provider_status.stale is False


@dataclass(frozen=True)
class StubProvider:
    metadata: FederationReadMetadata

    def read_metadata(self) -> FederationReadMetadata:
        return self.metadata


@dataclass(frozen=True)
class StubIncidentProvider:
    fallback_active: bool

    def source_metadata(self):
        from src.ui.incident_review.projection_source import ProjectionSourceMetadata

        return ProjectionSourceMetadata(
            source_type="file_projection",
            read_only=True,
            authority_coupled=False,
            fallback_active=self.fallback_active,
            source_ref="projection_snapshot.json",
        )

    def list_incidents(self):
        return []


def test_incident_provider_status_not_connected_when_fallback_active():
    default_service = ProjectionFederationService.build_default()
    incident_service = type(default_service._incident_service)(StubIncidentProvider(fallback_active=True))  # noqa: SLF001
    service = ProjectionFederationService(incident_service, default_service._providers)  # noqa: SLF001

    card = {item.key: item for item in service.report().cards}["incident_review"]
    assert card.status == "not_connected"
    assert card.provider_status.connected is False
    assert card.provider_status.stale is True
    assert card.provider_status.provider_kind == "StubIncidentProvider"


def test_provider_status_truthful_mapping_for_unavailable_provider_data():
    default_service = ProjectionFederationService.build_default()
    unavailable = StubProvider(
        metadata=FederationReadMetadata(
            label="Unavailable",
            status="not_connected",
            source_type="deterministic_fallback",
            fallback_active=True,
            item_count=0,
        )
    )
    providers = {
        key: unavailable
        for key in ["recovery", "simulation", "mesh", "policy", "replay", "system_health"]
    }
    service = ProjectionFederationService(default_service._incident_service, providers)  # noqa: SLF001

    card = {item.key: item for item in service.report().cards}["recovery"]
    assert card.status == "not_connected"
    assert card.provider_status.connected is False
    assert card.provider_status.stale is True


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
        "provider_status",
        "read_only",
        "authority_coupled",
        "source_type",
        "fallback_active",
        "item_count",
        "stable_order",
    ]
    assert list(first["provider_status"].keys()) == [
        "key",
        "status",
        "label",
        "source_ref",
        "provider_kind",
        "connected",
        "stale",
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/projections').status_code == 405
