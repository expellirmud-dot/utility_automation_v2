from fastapi.testclient import TestClient
from src.ui.ops_overview_api import app

client = TestClient(app)


def test_get_runtime_tasks_summary():
    res = client.get("/ops/api/runtime-tasks")
    assert res.status_code == 200
    data = res.json()
    assert "timestamp" in data
    assert "count" in data
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


def test_get_runtime_tasks_invalid_method():
    res = client.post("/ops/api/runtime-tasks")
    assert res.status_code == 405
