from __future__ import annotations

from dataclasses import dataclass

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
        return [{"id": "INC-001"}, {"id": "INC-002"}]


class _FlakyProvider:
    def __init__(self, metadata: FederationReadMetadata | None = None, should_raise: bool = False) -> None:
        self._metadata = metadata
        self._should_raise = should_raise

    def read_metadata(self) -> FederationReadMetadata:
        if self._should_raise:
            raise RuntimeError("provider unavailable")
        assert self._metadata is not None
        return self._metadata


# Canonical domain order fixture: incident_review, recovery, simulation, mesh, policy, replay, system_health

def test_projection_endpoint_ordering_and_fallback_stability(monkeypatch):
    providers = {
        "recovery": _FlakyProvider(
            FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type="recovery_projection",
                fallback_active=False,
                item_count=4,
            )
        ),
        "simulation": _FlakyProvider(
            FederationReadMetadata(
                label="Degraded",
                status="degraded",
                source_type="simulation_projection",
                fallback_active=True,
                item_count=1,
            )
        ),
        "mesh": _FlakyProvider(should_raise=True),
        "policy": _FlakyProvider(
            FederationReadMetadata(
                label="Disconnected",
                status="not_connected",
                source_type="policy_projection",
                fallback_active=False,
                item_count=0,
            )
        ),
        "replay": _FlakyProvider(
            FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type="replay_projection",
                fallback_active=False,
                item_count=3,
            )
        ),
        "system_health": _FlakyProvider(should_raise=True),
    }
    service = ProjectionFederationService(incident_service=_StubIncidentService(), providers=providers)
    monkeypatch.setattr(ops_overview_api, "_federation_service", service)

    client = TestClient(ops_overview_api.app)
    runs = [client.get("/ops/api/projections") for _ in range(3)]

    for response in runs:
        assert response.status_code == 200

    payloads = [response.json() for response in runs]

    key_order_runs = [[card["key"] for card in payload["cards"]] for payload in payloads]
    assert key_order_runs[0] == key_order_runs[1] == key_order_runs[2]

    domain_by_key_runs = [
        {card["key"]: card["domain"] for card in payload["cards"]}
        for payload in payloads
    ]
    assert domain_by_key_runs[0] == domain_by_key_runs[1] == domain_by_key_runs[2]

    expected_failure_cards = {
        card["key"]: {
            "fallback_active": card["fallback_active"],
            "fallback_reason": card["fallback_reason"],
            "status": card["status"],
            "source_type": card["source_type"],
            "item_count": card["item_count"],
        }
        for card in payloads[0]["cards"]
        if card["key"] in {"mesh", "system_health"}
    }
    for payload in payloads[1:]:
        run_failure_cards = {
            card["key"]: {
                "fallback_active": card["fallback_active"],
                "fallback_reason": card["fallback_reason"],
                "status": card["status"],
                "source_type": card["source_type"],
                "item_count": card["item_count"],
            }
            for card in payload["cards"]
            if card["key"] in {"mesh", "system_health"}
        }
        assert run_failure_cards == expected_failure_cards
