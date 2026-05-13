from pathlib import Path

from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory


def test_live_default_runtime_preference_and_fallback_metadata(tmp_path: Path):
    snapshot = tmp_path / "projection_snapshot.json"
    snapshot.write_text('{"incident_explorer": []}', encoding="utf-8")
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)
    metadata = provider.source_metadata()

    assert provider.__class__.__name__ == "LiveIncidentReviewProjectionProvider"
    assert metadata.read_only is True
    assert metadata.authority_coupled is False
    assert metadata.status_label == "file_projection_fallback"


def test_live_default_repeated_calls_equal_without_mock_incident_requirements(tmp_path: Path):
    snapshot = tmp_path / "projection_snapshot.json"
    snapshot.write_text('{"incident_explorer": []}', encoding="utf-8")
    provider = IncidentReviewProviderFactory.build_live_default(snapshot)

    first = provider.list_incidents()
    second = provider.list_incidents()

    assert first == second
