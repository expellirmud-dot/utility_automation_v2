from pathlib import Path

from fastapi.testclient import TestClient

from src.ui.incident_review.incident_review_api import app
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory


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


def test_repeated_calls_identical():
    client = TestClient(app)
    first = client.get('/incident-review/api/incidents').json()
    second = client.get('/incident-review/api/incidents').json()
    assert first == second


def test_mock_incidents_not_used_in_live_default(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer":[{"incident_id":"INC-LIVE-1","title":"x","severity":"LOW","status":"OPEN","summary":"s"}]}', encoding='utf-8')
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
