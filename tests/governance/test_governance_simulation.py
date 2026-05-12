from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.services.governance.simulation.simulation_api import router

def make_test_app():
    app = FastAPI()
    app.include_router(router)
    return app

client = TestClient(make_test_app())

def test_governance_simulation():
    payload = {
        "policy_id": "TEST_POL",
        "proposed_logic": {"val": 1},
        "scenario_name": "S1"
    }
    response = client.post("/simulation/simulate_policy_change_request", json=payload)
    assert response.status_code == 200
    print("Simulation: PASSED")

if __name__ == "__main__":
    test_governance_simulation()
