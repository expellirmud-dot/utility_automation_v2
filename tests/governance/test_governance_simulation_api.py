import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.services.governance.simulation.simulation_api import router

def make_test_app():
    app = FastAPI()
    app.include_router(router)
    return app

client = TestClient(make_test_app())

def test_simulation_api():
    # Test Policy Change
    payload = {
        "policy_id": "P1",
        "proposed_logic": {"action": "ALLOW"},
        "scenario_name": "TestScenario"
    }
    
    response = client.post("/simulation/simulate_policy_change_request", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert "simulation_hash" in report
    
    # Test Report Fetching
    get_res = client.get(f"/simulation/reports/{report['simulation_hash']}")
    assert get_res.status_code == 200
    assert get_res.json()["simulation_hash"] == report["simulation_hash"]
    
    print("Simulation API Flow: PASSED")

if __name__ == "__main__":
    test_simulation_api()
