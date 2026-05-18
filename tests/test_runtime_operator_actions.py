from fastapi.testclient import TestClient
from src.ui.ops_overview_api import app
import pytest

client = TestClient(app)

def test_api_create_task_invalid_payload():
    res = client.post("/ops/api/runtime-tasks/create", json={"task_id": "TASK-123"})
    # Missing required fields like title, objective, etc.
    assert res.status_code == 422

def test_api_start_task_invalid_payload():
    res = client.post("/ops/api/runtime-tasks/start", json={"task_id": "TASK-123"})
    # Missing actor_id
    assert res.status_code == 422

def test_api_finish_task_invalid_payload():
    res = client.post("/ops/api/runtime-tasks/finish", json={"task_id": "TASK-123"})
    # Missing worker_id and actual_output
    assert res.status_code == 422

def test_api_start_task_valid_payload_but_tool_fails():
    # If we provide a valid payload but the tool fails (e.g. no request file generated),
    # it should fail closed and return 500 with the tool's error dict.
    payload = {
        "task_id": "TASK-NONEXISTENT",
        "actor_id": "WORKER-01",
        "allow_read": ["src/"],
        "allow_write": ["src/"],
        "expected_output": ["out.py"]
    }
    res = client.post("/ops/api/runtime-tasks/start", json=payload)
    # The tool returns {"status": "FAILED"} and our adapter raises 500
    assert res.status_code == 500
    data = res.json()
    assert data["detail"]["status"] == "FAILED"
    assert "error" in data["detail"]
