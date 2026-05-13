from pathlib import Path

from fastapi.testclient import TestClient

from src.ui.incident_review.incident_review_api import app
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory
from src.ui.incident_review.runtime_projection_source import RuntimeProjectionSource


FORBIDDEN_IMPORTS = (
    'MeshOrchestrator',
    'PromotionPipeline',
    'RecoveryClassifier',
    'RecoveryPlanBuilder',
    'RecoverySimulationGate',
    'RecoveryProposalHandoff',
    'sqlite3.connect',
    'write_ledger',
)


def test_runtime_source_fallback_explicit(tmp_path: Path):
    fallback = tmp_path / 'fallback.json'
    fallback.write_text('{"incident_explorer":[{"incident_id":"INC-FB","title":"x","severity":"LOW","status":"OPEN","summary":"s"}]}', encoding='utf-8')
    runtime = RuntimeProjectionSource(runtime_projection_path=tmp_path / 'missing.json', fallback_source=IncidentReviewProviderFactory.build_file_backed_projection(fallback)._source)
    assert runtime.metadata.source_type == 'file_projection'


def test_live_default_prefers_runtime_projection(monkeypatch, tmp_path: Path):
    runtime_dir = tmp_path / 'ledger' / 'projections'
    runtime_dir.mkdir(parents=True)
    (runtime_dir / 'incident_review_projection.json').write_text('{"incident_explorer":[{"incident_id":"INC-RUNTIME","title":"x","severity":"LOW","status":"OPEN","summary":"s"}]}', encoding='utf-8')
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer":[{"incident_id":"INC-FALLBACK","title":"x","severity":"LOW","status":"OPEN","summary":"s"}]}', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)
    assert provider.metadata.source_type == 'runtime_projection'
    assert [item.incident_id for item in provider.list_incidents()] == ['INC-RUNTIME']


def test_repeated_calls_identical():
    client = TestClient(app)
    first = client.get('/incident-review/api/incidents').json()
    second = client.get('/incident-review/api/incidents').json()
    assert first == second


def test_mock_incidents_not_used_in_live_default(tmp_path: Path, monkeypatch):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer":[{"incident_id":"INC-LIVE-1","title":"x","severity":"LOW","status":"OPEN","summary":"s"}]}', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)
    assert [item.incident_id for item in provider.list_incidents()] == ['INC-LIVE-1']


def test_no_mutation_routes_registered():
    client = TestClient(app)
    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/incident-review/api/incidents').status_code == 405


def test_no_forbidden_imports_in_incident_review_path():
    for py_file in Path('src/ui/incident_review').glob('*.py'):
        content = py_file.read_text(encoding='utf-8')
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in content, f'{forbidden} in {py_file}'
