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


def test_provider_factory_uses_live_default(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer": []}', encoding='utf-8')
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)
    assert provider.__class__.__name__ == 'LiveIncidentReviewProjectionProvider'


def test_provider_exposes_source_metadata_without_private_access(tmp_path: Path):
    snapshot = tmp_path / 'snapshot.json'
    snapshot.write_text('{"incident_explorer": []}', encoding='utf-8')
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)
    metadata = provider.source_metadata()
    assert metadata.read_only is True
    assert metadata.authority_coupled is False
    assert metadata.fallback_active is True
