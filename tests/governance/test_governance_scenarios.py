from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.services.governance.simulation.simulation_api import router

def make_test_app():
    app = FastAPI()
    app.include_router(router)
    return app

client = TestClient(make_test_app())

def test_governance_scenarios():
    payload = [{
        "policy_id": "P1",
        "proposed_logic": {"val": 1},
        "scenario_name": "S1"
    }, {
        "policy_id": "P2",
        "proposed_logic": {"val": 2},
        "scenario_name": "S2"
    }]
    
    response = client.post("/simulation/simulate_scenarios_request", json=payload)
    assert response.status_code == 200
    hashes = response.json()
    assert len(hashes) == 2
    print("Scenarios: PASSED")

if __name__ == "__main__":
    test_governance_scenarios()
