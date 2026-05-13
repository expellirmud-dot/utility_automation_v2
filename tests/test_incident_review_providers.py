from pathlib import Path

from src.ui.incident_review.projection_providers import (
    IncidentReviewProviderFactory,
    LiveIncidentReviewProjectionProvider,
)
from src.ui.incident_review.projection_source import JsonFileProjectionSource


def test_projection_provider_empty_snapshot(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{}', encoding='utf-8')
    live = LiveIncidentReviewProjectionProvider(JsonFileProjectionSource(snapshot))
    assert live.list_incidents() == []


def test_projection_provider_deterministic_ordering(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text(
        '{"incident_explorer": ['
        '{"incident_id":"INC-9","title":"t","severity":"LOW","status":"OPEN","summary":"s"},'
        '{"incident_id":"INC-1","title":"t","severity":"LOW","status":"OPEN","summary":"s"}'
        '] }',
        encoding='utf-8',
    )
    live = LiveIncidentReviewProjectionProvider(JsonFileProjectionSource(snapshot))
    assert [x.incident_id for x in live.list_incidents()] == ['INC-1', 'INC-9']


def test_provider_factory_live_default_has_read_only_metadata():
    provider = IncidentReviewProviderFactory.build_live_default(Path('src/ui/incident_review/projection_snapshot.json'))
    assert provider.metadata.read_only is True
    assert provider.metadata.authority_coupled is False


def test_provider_factory_file_backed_projection_type(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer": []}', encoding='utf-8')
    provider = IncidentReviewProviderFactory.build_file_backed_projection(snapshot)
    assert provider.metadata.source_type == 'file_projection'
