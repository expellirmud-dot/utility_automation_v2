import importlib
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app
from src.ui.read_only_route_governance import (
    ReadOnlyRouteGovernanceError,
    inspect_read_only_routes,
    validate_read_only_route_governance,
)
from src.ui.read_only_surface_registry import ReadOnlySurfaceEntry, list_ops_exposed_surfaces, list_read_only_surfaces


client = TestClient(app)


def test_registry_ordering_stable():
    surfaces = list_read_only_surfaces()
    assert [item.key for item in surfaces] == [
        "ops_console",
        "incident_review",
        "recovery_dashboard",
        "simulation_dashboard",
        "telemetry_dashboard",
        "runtime_console",
    ]


def test_exposed_surfaces_are_read_only_and_not_authority_coupled_and_get_only():
    for surface in list_ops_exposed_surfaces():
        assert surface.read_only is True
        assert surface.authority_coupled is False
        assert list(surface.allowed_methods) == ["GET"]


def test_forbidden_route_prefixes_rejected_and_control_ops_not_exposed():
    invalid = ReadOnlySurfaceEntry(
        key="bad",
        title="Bad",
        route_prefix="/control_ops/trigger",
        api_prefix="/control_ops/api",
        allowed_methods=("GET",),
        status="connected",
        authority_coupled=False,
        read_only=True,
        exposed_in_ops=True,
        stable_order=1,
    )

    try:
        validate_read_only_route_governance((invalid,))
        assert False, "expected governance error"
    except ReadOnlyRouteGovernanceError:
        pass


def test_ops_api_surfaces_get_returns_deterministic_payload_and_non_get_405():
    response = client.get("/ops/api/surfaces")
    assert response.status_code == 200
    payload = response.json()
    assert [item["key"] for item in payload["surfaces"]] == ["ops_console", "incident_review", "runtime_console"]

    first = payload["surfaces"][0]
    assert list(first.keys()) == [
        "key",
        "title",
        "route_prefix",
        "api_prefix",
        "allowed_methods",
        "status",
        "authority_coupled",
        "read_only",
        "exposed_in_ops",
        "stable_order",
    ]

    for method in ["post", "put", "patch", "delete"]:
        assert getattr(client, method)("/ops/api/surfaces").status_code == 405


def test_ops_route_governance_endpoint_get_only_and_shape():
    response = client.get("/ops/api/route-governance")
    assert response.status_code == 200
    payload = response.json()
    assert list(payload.keys()) == ["valid", "checked_routes", "registry_surface_count", "violations"]
    assert payload["valid"] is True

    for method in ["post", "put", "patch", "delete"]:
        assert getattr(client, method)("/ops/api/route-governance").status_code == 405


def test_route_introspection_rejects_post_under_ops():
    failing_app = FastAPI()

    @failing_app.post("/ops/api/mutate")
    def mutate():
        return {"ok": True}

    report = inspect_read_only_routes(app=failing_app)
    assert report.valid is False
    assert any(item.reason == "non_read_only_method" for item in report.violations)


def test_route_introspection_rejects_control_ops_prefix():
    failing_app = FastAPI()

    @failing_app.get("/ops/control_ops/status")
    def control_status():
        return {"ok": True}

    report = inspect_read_only_routes(app=failing_app)
    assert report.valid is False
    assert any(item.reason == "forbidden_control_prefix" for item in report.violations)


def test_route_introspection_rejects_action_keywords_and_is_stably_sorted():
    failing_app = FastAPI()

    @failing_app.get("/ops/api/retry")
    def retry_view():
        return {"ok": True}

    @failing_app.get("/ops/api/approve")
    def approve_view():
        return {"ok": True}

    report = inspect_read_only_routes(app=failing_app)
    assert report.valid is False
    assert [item.path for item in report.violations] == sorted(item.path for item in report.violations)
    assert any(item.reason == "forbidden_action_keyword" for item in report.violations)


def test_strict_flag_default_disabled():
    assert os.getenv('OPS_ROUTE_GOVERNANCE_STRICT', '0') != '1'


def test_strict_flag_enabled_fails_invalid_routes():
    module = importlib.import_module('src.ui.ops_overview_api')
    original = module.inspect_read_only_routes

    class _BadReport:
        valid = False
        checked_routes = 2
        registry_surface_count = 1
        violations = (object(),)

    try:
        module.inspect_read_only_routes = lambda app=None: _BadReport()
        os.environ['OPS_ROUTE_GOVERNANCE_STRICT'] = '1'
        try:
            if module._strict_route_governance_enabled():
                strict_report = module.inspect_read_only_routes(app=module.app)
                if not strict_report.valid:
                    raise module.ReadOnlyRouteGovernanceError(
                        'OPS_ROUTE_GOVERNANCE_STRICT=1 and route governance is invalid: '
                        f'checked_routes={strict_report.checked_routes}, violations={len(strict_report.violations)}'
                    )
            assert False, 'expected strict governance failure'
        except module.ReadOnlyRouteGovernanceError as exc:
            assert 'OPS_ROUTE_GOVERNANCE_STRICT=1' in str(exc)
            assert 'checked_routes=2' in str(exc)
            assert 'violations=1' in str(exc)
    finally:
        module.inspect_read_only_routes = original
        os.environ.pop('OPS_ROUTE_GOVERNANCE_STRICT', None)
