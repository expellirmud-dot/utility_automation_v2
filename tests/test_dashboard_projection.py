from fastapi.testclient import TestClient

from src.services.control_plane.api.gov_control_app import app
from src.services.dashboard.projection_repository import DashboardProjectionRepository
from src.services.dashboard.projection_seed import DASHBOARD_BUCKET
from src.services.dashboard.projection_service import DashboardProjectionService
from src.storage.database.database_manager import DatabaseManager


def configure_temp_db(monkeypatch, tmp_path):
    db_path = tmp_path / "utility_automation.db"
    monkeypatch.setattr(DatabaseManager, "DB_PATH", str(db_path))
    return db_path


def test_schema_initializes_and_seed_is_idempotent(monkeypatch, tmp_path):
    configure_temp_db(monkeypatch, tmp_path)
    repository = DashboardProjectionRepository()
    service = DashboardProjectionService(repository=repository)

    first_seeded = service.ensure_seeded()
    first_count = repository.count_bucket(DASHBOARD_BUCKET)
    second_seeded = service.ensure_seeded()
    second_count = repository.count_bucket(DASHBOARD_BUCKET)

    assert first_seeded is True
    assert second_seeded is False
    assert first_count == second_count
    assert first_count > 0


def test_projection_response_is_stable_and_ordered(monkeypatch, tmp_path):
    configure_temp_db(monkeypatch, tmp_path)
    service = DashboardProjectionService()

    first = service.projection()
    second = service.projection()

    assert first == second
    assert first["bucket"] == DASHBOARD_BUCKET
    assert first["generated_by"] == "deterministic_seed"
    assert first["seed"] == 41041
    assert [item["key"] for item in first["stats"]] == [
        "health",
        "incidents",
        "replay",
        "review_time",
    ]
    assert len(first["throughput"]["bars"]) == 8
    assert len(first["activity"]) == 4
    assert [item["id"] for item in first["incidents"]] == [
        "INC-1042",
        "INC-1039",
        "INC-1031",
        "INC-1027",
    ]


def test_dashboard_projection_api_is_get_only(monkeypatch, tmp_path):
    configure_temp_db(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/dashboard/projection")
    assert response.status_code == 200
    assert response.json()["bucket"] == DASHBOARD_BUCKET

    for method in ["post", "put", "patch", "delete"]:
        blocked = getattr(client, method)("/dashboard/projection")
        assert blocked.status_code == 405
