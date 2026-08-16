import ast
import re
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app


client = TestClient(app)

PANEL_ROUTES = (
    "/ops/api/recovery",
    "/ops/api/simulation",
    "/ops/api/mesh",
    "/ops/api/policy",
    "/ops/api/replay",
    "/ops/api/system-health",
    "/ops/api/panels",
)

PANEL_MODULES = (
    "src/projections/db_projection_reader.py",
    "src/ui/domain_panels/formatters.py",
    "src/ui/ops_overview_api.py",
)


def _module_import_names(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_all_ops_domain_panel_routes_are_get_only():
    for route in PANEL_ROUTES:
        assert client.get(route).status_code == 200
        for method in ("post", "put", "patch", "delete"):
            assert getattr(client, method)(route).status_code == 405


def test_no_mutation_routes_are_exposed_under_ops_api():
    forbidden = ("approve", "reject", "retry", "execute", "repair", "promote", "control")
    for route in app.routes:
        path = getattr(route, "path", "").lower()
        if not path.startswith("/ops/api"):
            continue
        assert not any(token in path for token in forbidden)


def test_panel_modules_do_not_import_authority_or_control_paths():
    forbidden = (
        "control_ops",
        "meshorchestrator",
        "executor",
        "repair",
        "promotion",
        "replay_trigger",
        "write_ledger",
    )
    for module_path in PANEL_MODULES:
        imported_blob = "\n".join(sorted(_module_import_names(module_path))).lower()
        source_blob = Path(module_path).read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in imported_blob
            assert token not in source_blob


def test_database_reader_is_projection_only_and_not_source_of_truth(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "projection.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE recovery_projection (id TEXT PRIMARY KEY, label TEXT)")
        conn.execute("INSERT INTO recovery_projection (id, label) VALUES ('r-1', 'Recovery item')")

    monkeypatch.setenv("OPS_PROJECTION_DB_PATH", str(db_path))
    payload = client.get("/ops/api/recovery").json()

    assert payload["status"] == "connected"
    assert payload["item_count"] == 1
    assert payload["metadata"]["projection_only"] is True
    assert payload["metadata"]["source_of_truth"] == "ledger"
    assert payload["metadata"]["database_role"] == "cache_projection"
    assert payload["advisory_only"] is True


def test_bundled_panels_are_deterministic_and_use_stable_shape(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "projection.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE replay_projection (id TEXT PRIMARY KEY, stable_order INTEGER)")
        conn.executemany(
            "INSERT INTO replay_projection (id, stable_order) VALUES (?, ?)",
            [("replay-b", 20), ("replay-a", 10)],
        )

    monkeypatch.setenv("OPS_PROJECTION_DB_PATH", str(db_path))
    first = client.get("/ops/api/panels").json()
    second = client.get("/ops/api/panels").json()

    assert first == second
    assert [panel["domain"] for panel in first["panels"]] == [
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]
    replay = {panel["domain"]: panel for panel in first["panels"]}["replay"]
    assert [item["id"] for item in replay["items"]] == ["replay-a", "replay-b"]


def test_database_reader_contains_no_mutation_sql():
    source = Path("src/projections/db_projection_reader.py").read_text(encoding="utf-8").upper()
    for keyword in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE"):
        assert re.search(rf"\b{keyword}\b", source) is None
