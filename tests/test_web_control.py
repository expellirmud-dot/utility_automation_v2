import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from src.services.web_control.server import app, event_stream

client = TestClient(app)

def test_get_state():
    response = client.get("/api/state")
    assert response.status_code == 200
    assert response.json()["system_status"] == "STABLE"

def test_override_decision():
    response = client.post("/api/override?decision_id=123&action=DENY")
    assert response.status_code == 200
    assert response.json()["overridden"] is True
    assert response.json()["id"] == "123"

def test_pause_healing():
    response = client.post("/api/healing/pause")
    assert response.status_code == 200
    assert response.json()["paused"] is True

def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("pause")
        data = websocket.receive_text()
        assert "paused" in data or "True" in data
