from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.services.observability.api.incident_review_api import router
from src.services.observability.incident_review.provider import IncidentReviewProvider, MockIncidentReviewProvider
from src.services.observability.incident_review.service import IncidentReviewService


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_endpoints_stable_payloads() -> None:
    client = _client()
    incidents = client.get("/api/incident-review/incidents")
    analytics = client.get("/api/incident-review/incidents/analytics")
    detail = client.get("/api/incident-review/incidents/INC-001")

    assert incidents.status_code == 200
    assert incidents.json() == {
        "incidents": [
            {"incident_id": "INC-001", "severity": "high", "status": "open", "summary": "Transformer drift anomaly."},
            {"incident_id": "INC-002", "severity": "medium", "status": "investigating", "summary": "Telemetry lag exceeding SLA."},
        ]
    }
    assert analytics.status_code == 200
    assert analytics.json() == {"total_incidents": 2, "severity_counts": {"high": 1, "medium": 1}}
    assert detail.status_code == 200
    assert detail.json()["incident_id"] == "INC-001"


def test_non_get_methods_return_405() -> None:
    client = _client()
    for method in (client.post, client.put, client.patch, client.delete):
        assert method("/api/incident-review/incidents").status_code == 405
        assert method("/api/incident-review/incidents/analytics").status_code == 405


def test_analytics_route_precedence_over_dynamic_incident_id() -> None:
    client = _client()
    response = client.get("/api/incident-review/incidents/analytics")
    assert response.status_code == 200
    assert "total_incidents" in response.json()


def test_empty_provider_deterministic_payloads() -> None:
    service = IncidentReviewService(provider=IncidentReviewProvider(incidents=[]))
    assert service.get_incidents() == []
    assert service.get_analytics() == {"total_incidents": 0, "severity_counts": {}}
    assert service.get_incident("INC-404") is None


def test_mock_provider_repeated_calls_identical() -> None:
    service = IncidentReviewService(provider=MockIncidentReviewProvider())
    assert service.get_incidents() == service.get_incidents()
    assert service.get_analytics() == service.get_analytics()


def test_no_write_capable_runtime_imports() -> None:
    service_text = Path("src/services/observability/incident_review/service.py").read_text()
    api_text = Path("src/services/observability/api/incident_review_api.py").read_text()
    forbidden = ["MeshOrchestrator", "PromotionPipeline", "append_event", "commit_event", "write_ledger"]
    for token in forbidden:
        assert token not in service_text
        assert token not in api_text


def test_frontend_read_only_constraints() -> None:
    files = [
        Path("src/ui/templates/review_queue.html"),
        Path("src/ui/cdml_dashboard.html"),
        Path("src/ui/dashboard/templates/index.html"),
    ]
    scan = "\n".join(path.read_text() for path in files if path.exists())
    lowered = scan.lower()
    assert "innerhtml" not in lowered
    assert "<form" not in lowered
    assert "method=\"post\"" not in lowered
    assert "method:'post'" not in lowered
    assert "method: 'post'" not in lowered
    assert "action=" not in lowered
