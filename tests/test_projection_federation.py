import ast
from dataclasses import dataclass
import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app
from src.ui.projection_federation import ProjectionFederationService
from src.ui.projection_federation_providers import FederationReadMetadata


client = TestClient(app)


CONTRACT_FIXTURE_PATH = Path(__file__).resolve().parent / "projections_contract_fixture.json"


def _load_projection_contract_fixture() -> dict:
    return json.loads(CONTRACT_FIXTURE_PATH.read_text(encoding="utf-8"))


def _validate_status_vocab(statuses: list[str], allowed: set[str]) -> None:
    unknown = sorted(set(statuses) - allowed)
    assert not unknown, f"Unknown projection status values in contract fixture: {unknown}"


def test_federation_stable_order_and_read_only_contract():
    report = ProjectionFederationService.build_default().report()
    assert [card.key for card in report.cards] == [
        "incident_review",
        "recovery",
        "simulation",
        "mesh",
        "policy",
        "replay",
        "system_health",
    ]
    assert [card.stable_order for card in report.cards] == [10, 20, 30, 40, 50, 60, 70]
    assert all(card.read_only is True for card in report.cards)
    assert all(card.authority_coupled is False for card in report.cards)


def test_incident_and_domain_providers_connected_deterministically(monkeypatch):
    from src.services.governance.simulation import simulation_api

    monkeypatch.setattr(simulation_api, "_simulation_reports", {"sim-1": {"simulation_hash": "sim-1"}})
    cards = ProjectionFederationService.build_default().report().cards
    by_key = {card.key: card for card in cards}

    assert by_key["incident_review"].status == "connected"
    assert by_key["incident_review"].source_type in {"runtime_projection", "file_projection"}
    assert by_key["incident_review"].provider_status.connected is True

    expected = {
        "recovery": (2, "Connected", "connected", "recovery_read_model"),
        "simulation": (1, "Connected", "connected", "simulation_read_model"),
        "mesh": (3, "Connected", "connected", "mesh_read_model"),
        "policy": (1, "Connected", "connected", "policy_read_model"),
        "replay": (2, "Connected", "connected", "replay_read_model"),
        "system_health": (1, "Connected", "connected", "system_health_telemetry"),
    }
    for key, (count, label, status, source_type) in expected.items():
        card = by_key[key]
        assert card.item_count == count
        assert card.label == label
        assert card.status == status
        assert card.source_type == source_type
        assert card.fallback_active is False
        assert card.provider_status.source_ref == source_type
        assert card.provider_status.connected is True
        assert card.provider_status.stale is False


@dataclass(frozen=True)
class StubProvider:
    metadata: FederationReadMetadata

    def read_metadata(self) -> FederationReadMetadata:
        return self.metadata


def test_provider_status_truthful_mapping_for_unavailable_provider_data():
    default_service = ProjectionFederationService.build_default()
    unavailable = StubProvider(
        metadata=FederationReadMetadata(
            label="Unavailable",
            status="not_connected",
            source_type="deterministic_fallback",
            fallback_active=True,
            item_count=0,
        )
    )
    providers = {
        key: unavailable
        for key in ["recovery", "simulation", "mesh", "policy", "replay", "system_health"]
    }
    service = ProjectionFederationService(default_service._incident_service, providers)  # noqa: SLF001

    card = {item.key: item for item in service.report().cards}["recovery"]
    assert card.status == "not_connected"
    assert card.provider_status.connected is False
    assert card.provider_status.stale is True


def test_ops_projections_get_only_and_shape():
    response = client.get('/ops/api/projections')
    assert response.status_code == 200
    payload = response.json()
    assert list(payload.keys()) == ["cards"]

    first = payload["cards"][0]
    assert list(first.keys()) == [
        "key",
        "title",
        "domain",
        "status",
        "label",
        "provider_status",
        "read_only",
        "authority_coupled",
        "source_type",
        "fallback_active",
        "fallback_reason",
        "item_count",
        "stable_order",
    ]
    assert list(first["provider_status"].keys()) == [
        "key",
        "status",
        "label",
        "source_ref",
        "provider_kind",
        "connected",
        "stale",
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/projections').status_code == 405


class _OkProvider:
    def read_metadata(self):
        class _Meta:
            status = "connected"
            label = "Connected"
            source_type = "ok_source"
            fallback_active = False
            item_count = 7

        return _Meta()


class _FailProvider:
    def read_metadata(self):
        raise RuntimeError("sensitive provider internals")


class _TimeoutProvider:
    def read_metadata(self):
        raise TimeoutError("request timeout")


def test_one_provider_failure_is_isolated_and_endpoint_stays_200(monkeypatch):
    original_builder = ProjectionFederationService.build_default

    def _build_faulty():
        service = original_builder()
        providers = dict(service._providers)
        providers["mesh"] = _FailProvider()
        providers["policy"] = _OkProvider()
        return ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    monkeypatch.setattr("src.ui.ops_overview_api.ProjectionFederationService.build_default", _build_faulty)

    from src.ui import ops_overview_api

    ops_overview_api._federation_service = _build_faulty()
    response = client.get('/ops/api/projections')

    assert response.status_code == 200
    cards = {item["key"]: item for item in response.json()["cards"]}
    assert cards["mesh"]["status"] == "degraded"
    assert cards["mesh"]["fallback_active"] is True
    assert cards["policy"]["status"] == "connected"
    assert cards["policy"]["item_count"] == 7
    assert "traceback" not in response.text.lower()


def test_fallback_payload_is_deterministic_for_same_failure():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["simulation"] = _FailProvider()
    unstable = ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    first = {c.key: c for c in unstable.report().cards}["simulation"]
    second = {c.key: c for c in unstable.report().cards}["simulation"]

    assert first == second
    assert first.fallback_reason == "provider_exception"


def test_failure_status_is_truthful_degraded_or_not_connected():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["replay"] = _FailProvider()
    unstable = ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    failing_card = {c.key: c for c in unstable.report().cards}["replay"]
    assert failing_card.status in {"degraded", "not_connected"}


def test_provider_failure_emits_one_structured_event_per_failed_provider():
    service = ProjectionFederationService.build_default()
    providers = dict(service._providers)
    providers["simulation"] = _FailProvider()
    providers["replay"] = _TimeoutProvider()

    emitted = []

    def _emit(metadata):
        emitted.append(metadata)

    unstable = ProjectionFederationService(
        incident_service=service._incident_service,
        providers=providers,
        failure_emitter=_emit,
    )

    report = unstable.report()
    cards = {c.key: c for c in report.cards}
    assert cards["simulation"].status == "degraded"
    assert cards["replay"].status == "degraded"

    assert len(emitted) == 2
    by_key = {item.provider_key: item for item in emitted}
    assert set(by_key) == {"simulation", "replay"}
    assert by_key["simulation"].failure_class == "unexpected"
    assert by_key["replay"].failure_class == "timeout"
    assert by_key["simulation"].correlation_id is None


def test_api_payload_does_not_leak_provider_stack_traces(monkeypatch):
    original_builder = ProjectionFederationService.build_default

    def _build_faulty():
        service = original_builder()
        providers = dict(service._providers)
        providers["mesh"] = _FailProvider()
        return ProjectionFederationService(incident_service=service._incident_service, providers=providers)

    monkeypatch.setattr("src.ui.ops_overview_api.ProjectionFederationService.build_default", _build_faulty)

    from src.ui import ops_overview_api

    ops_overview_api._federation_service = _build_faulty()
    response = client.get('/ops/api/projections')

    assert response.status_code == 200
    payload_text = response.text.lower()
    assert "traceback" not in payload_text
    assert "sensitive provider internals" not in payload_text

def test_ops_projection_contract_snapshot_and_backward_compatibility_guard():
    fixture = _load_projection_contract_fixture()
    status_vocab = set(fixture["deterministic_status_vocabulary"])

    response = client.get('/ops/api/projections')
    assert response.status_code == 200
    cards = response.json()["cards"]
    assert cards

    provider_required = set(fixture["ProjectionProviderStatus"]["required_fields"])

    for card in cards:
        provider_status = card["provider_status"]
        missing_provider_fields = provider_required - set(provider_status.keys())
        assert not missing_provider_fields, (
            "ProjectionProviderStatus contract changed (field removal/rename): "
            f"{sorted(missing_provider_fields)}"
        )

        assert card["status"] in status_vocab
        assert provider_status["status"] in status_vocab

        assert card["key"] == provider_status["key"]
        assert card["label"] == provider_status["label"]
        assert card["source_type"] == provider_status["source_ref"]
        assert isinstance(provider_status["connected"], bool)
        assert isinstance(provider_status["stale"], bool)


def test_projection_contract_fixture_rejects_unknown_status_values():
    fixture = _load_projection_contract_fixture()
    allowed = set(fixture["deterministic_status_vocabulary"])

    _validate_status_vocab(fixture["ProjectionProviderStatus"]["status_values"], allowed)
    _validate_status_vocab(fixture["ProjectionSummaryCard"]["status_values"], allowed)

    mutated = list(fixture["ProjectionProviderStatus"]["status_values"]) + ["flaky"]
    try:
        _validate_status_vocab(mutated, allowed)
    except AssertionError as exc:
        assert "Unknown projection status values" in str(exc)
    else:
        raise AssertionError("Expected unknown status validation to fail")


ADAPTER_MODULES = (
    "src/ui/projection_federation_providers.py",
    "src/ui/incident_review/projection_providers.py",
    "src/ui/incident_review/projection_source.py",
)

FORBIDDEN_IMPORT_PATTERNS = (
    "control_plane",
    "authority",
    "mesh_orchestrator",
    "integrated_control_plane",
    "dashboard_api",
    "control_actions",
)


def _module_import_names(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def test_task_045_adapter_forbidden_import_guards_s4_to_s6_modules():
    for module_path in ADAPTER_MODULES:
        imports = _module_import_names(module_path)
        imported_blob = "\n".join(sorted(imports)).lower()
        for forbidden in FORBIDDEN_IMPORT_PATTERNS:
            assert forbidden not in imported_blob, (
                f"{module_path} must not import control-plane/authority mutation modules containing: {forbidden}"
            )


def test_task_045_federation_wide_forbidden_import_aggregate_guard():
    imported_blob = "\n".join(
        sorted({name for path in ADAPTER_MODULES for name in _module_import_names(path)})
    ).lower()
    offenders = [item for item in FORBIDDEN_IMPORT_PATTERNS if item in imported_blob]
    assert not offenders, f"Federation adapter import graph includes forbidden modules: {offenders}"


def test_task_045_ops_projection_routes_do_not_expose_mutation_actions():
    for path in ("/ops/api/overview", "/ops/api/projections"):
        for method in ("post", "put", "patch", "delete"):
            response = getattr(client, method)(path)
            assert response.status_code == 405, f"{method.upper()} {path} unexpectedly exposed"


def test_task_045_federation_cards_never_report_mutation_capable_flags():
    payload = client.get("/ops/api/projections").json()
    cards = payload["cards"]
    assert cards
    for card in cards:
        assert card["read_only"] is True
        assert card["authority_coupled"] is False


def test_task_045_ops_federation_paths_do_not_fallback_to_legacy_authority_services():
    for module_path in ("src/ui/ops_overview_api.py", "src/ui/projection_federation.py"):
        imports = _module_import_names(module_path)
        imported_blob = "\n".join(sorted(imports)).lower()
        for forbidden in FORBIDDEN_IMPORT_PATTERNS:
            assert forbidden not in imported_blob, (
                f"{module_path} must remain federation-only and not import legacy direct authority services ({forbidden})"
            )
