import pytest
import ast
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.ui.dashboard.simulation_routes import router

def make_test_app():
    app = FastAPI()
    app.include_router(router)
    return app

client = TestClient(make_test_app())

FORBIDDEN_SYMBOLS = [
    "PromotionPipeline", "MeshOrchestrator", "submit_critical_event",
    "promote", "append_event", "propose_event", "commit_event", "write_ledger"
]

def test_routes_are_get_only():
    # Only GET routes are defined in this router
    for route in router.routes:
        assert "GET" in route.methods, f"Route {route.path} is not GET-only"

def test_forbidden_symbols():
    with open("src/ui/dashboard/simulation_routes.py", "r") as f:
        tree = ast.parse(f.read())
        
    for node in ast.walk(tree):
        if isinstance(node, (ast.Name, ast.Attribute)):
            name = getattr(node, 'id', getattr(node, 'attr', None))
            if name in FORBIDDEN_SYMBOLS:
                pytest.fail(f"Forbidden symbol {name} found in dashboard routes!")

def test_deterministic_ordering():
    # Seed dummy reports to check ordering
    from src.services.governance.simulation.simulation_api import _simulation_reports
    _simulation_reports["hash_b"] = {"simulation_hash": "hash_b"}
    _simulation_reports["hash_a"] = {"simulation_hash": "hash_a"}
    
    response = client.get("/simulation/dashboard")
    assert response.status_code == 200
    # Check if hash_a comes before hash_b in the rendered HTML (alphabetical order)
    assert response.text.find("hash_a") < response.text.find("hash_b")

def test_empty_state_safe():
    # Clear reports for this test
    from src.services.governance.simulation.simulation_api import _simulation_reports
    _simulation_reports.clear()
    
    response = client.get("/simulation/dashboard")
    assert response.status_code == 200

def test_report_lookup():
    # Simulate a report exists
    from src.services.governance.simulation.simulation_api import _simulation_reports
    _simulation_reports["test_hash"] = {
        "simulation_hash": "test_hash", 
        "impact": {"status": "simulated"},
        "manual_review_required": True,
        "warnings": ["w1"]
    }
    
    response = client.get("/simulation/detail/test_hash")
    assert response.status_code == 200
    assert "test_hash" in response.text
    assert "ADVISORY ONLY" in response.text
