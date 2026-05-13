from __future__ import annotations

import ast

from fastapi.testclient import TestClient

from src.ui import ops_overview_api
from src.services.governance.simulation import simulation_api


client = TestClient(ops_overview_api.app)


def test_recovery_and_simulation_adapters_report_truthful_connected_state(monkeypatch):
    monkeypatch.setattr(simulation_api, "_simulation_reports", {"r1": {"simulation_hash": "r1"}, "r2": {"simulation_hash": "r2"}})

    response = client.get("/ops/api/projections")
    assert response.status_code == 200

    cards = {item["key"]: item for item in response.json()["cards"]}

    recovery = cards["recovery"]
    assert recovery["status"] == "connected"
    assert recovery["provider_status"]["connected"] is True
    assert recovery["source_type"] == "recovery_read_model"

    simulation = cards["simulation"]
    assert simulation["status"] == "connected"
    assert simulation["provider_status"]["connected"] is True
    assert simulation["item_count"] == 2
    assert simulation["source_type"] == "simulation_read_model"


def test_simulation_adapter_degrades_when_read_model_is_unavailable(monkeypatch):
    monkeypatch.setattr(simulation_api, "_simulation_reports", None)

    response = client.get("/ops/api/projections")
    assert response.status_code == 200

    simulation = {item["key"]: item for item in response.json()["cards"]}["simulation"]
    assert simulation["status"] == "degraded"
    assert simulation["provider_status"]["connected"] is False
    assert simulation["item_count"] == 0


def test_s4_adapters_forbidden_import_guards():
    file_path = "src/ui/projection_federation_providers.py"
    tree = ast.parse(open(file_path, encoding="utf-8").read())

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden_prefixes = (
        "src.services.governance.recovery.recovery_handoff",
        "src.services.governance.recovery.recovery_plan_builder",
        "src.services.governance.simulation.governance_simulation_engine",
    )
    for module in imported:
        assert not module.startswith(forbidden_prefixes), module


def test_overview_and_projections_consistent_when_simulation_degraded(monkeypatch):
    monkeypatch.setattr(simulation_api, "_simulation_reports", None)

    projections = client.get("/ops/api/projections")
    overview = client.get("/ops/api/overview")

    assert projections.status_code == 200
    assert overview.status_code == 200

    proj_sim = {item["key"]: item for item in projections.json()["cards"]}["simulation"]
    over_sim = {item["key"]: item for item in overview.json()["cards"]}["simulation"]
    assert proj_sim["status"] == over_sim["status"] == "degraded"
