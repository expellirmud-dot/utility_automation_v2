from pathlib import Path

from fastapi.testclient import TestClient

from src.services.control_plane.api.gov_control_app import app
from src.services.ops_console.db_projection_reader import OpsProjectionReader


OPS_ROUTES = [
    "/ops/api/recovery",
    "/ops/api/simulation",
    "/ops/api/mesh",
    "/ops/api/policy",
    "/ops/api/replay",
    "/ops/api/system-health",
    "/ops/api/panels",
]


def test_ops_domain_panel_routes_are_get_only(monkeypatch, tmp_path):
    import src.services.ops_console.api as ops_api

    monkeypatch.setattr(ops_api, "reader", OpsProjectionReader(str(tmp_path / "missing.db")))
    client = TestClient(app)

    for route in OPS_ROUTES:
        response = client.get(route)
        assert response.status_code == 200

        for method in ["post", "put", "patch", "delete"]:
            blocked = getattr(client, method)(route)
            assert blocked.status_code == 405


def test_ops_domain_panel_payloads_are_advisory_only(monkeypatch, tmp_path):
    import src.services.ops_console.api as ops_api

    monkeypatch.setattr(ops_api, "reader", OpsProjectionReader(str(tmp_path / "missing.db")))
    client = TestClient(app)

    bundled = client.get("/ops/api/panels").json()
    assert bundled["advisory_only"] is True
    assert bundled["panel_count"] == 6

    for panel in bundled["panels"]:
        assert panel["advisory_only"] is True
        assert panel["diagnostics"]["projection_only"] is True
        assert panel["item_count"] == 0
        assert panel["recommendations"] == []

    forbidden_words = {"approve", "reject", "retry", "execute", "repair", "promote"}
    flattened = " ".join(_flatten_values(bundled)).lower()
    for word in forbidden_words:
        assert word not in flattened


def test_ops_domain_panel_sources_avoid_authority_imports_and_mutation_routes():
    api_source = Path("src/services/ops_console/api.py").read_text()
    reader_source = Path("src/services/ops_console/db_projection_reader.py").read_text()
    formatter_source = Path("src/services/ops_console/formatters.py").read_text()
    combined = "\n".join([api_source, reader_source, formatter_source])

    for marker in ["@router.post", "@router.put", "@router.patch", "@router.delete"]:
        assert marker not in api_source

    for forbidden in [
        "control_ops",
        "MeshOrchestrator",
        "RecoveryClassifier",
        "RecoveryPlanBuilder",
        "RecoverySimulationGate",
        "RecoveryProposalHandoff",
        "PromotionPipeline",
        "write_ledger",
        "append_event",
        "commit_event",
    ]:
        assert forbidden not in combined

    for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]:
        assert keyword not in reader_source


def _flatten_values(value) -> list[str]:
    if isinstance(value, dict):
        output = []
        for key, nested in value.items():
            output.append(str(key))
            output.extend(_flatten_values(nested))
        return output
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(_flatten_values(item))
        return output
    return [str(value)]
