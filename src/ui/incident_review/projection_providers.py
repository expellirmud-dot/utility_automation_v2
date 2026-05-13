from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .incident_review_models import IncidentReviewItem
from .projection_source import IncidentReviewProjectionSource, JsonFileProjectionSource
from .runtime_projection_source import ProjectionSourceMetadata, RuntimeProjectionSource


@dataclass(frozen=True)
class ProviderMetadata:
    source_type: str
    read_only: bool
    authority_coupled: bool


class SnapshotIncidentReviewProvider:
    def __init__(self, snapshot_path: Path) -> None:
        self._source = JsonFileProjectionSource(snapshot_path)
        self.metadata = ProviderMetadata("snapshot_test", True, False)

    def list_incidents(self) -> list[IncidentReviewItem]:
        snapshot = self._source.read_snapshot()
        return [
            IncidentReviewItem(
                incident_id=item["incident_id"],
                title=item["title"],
                severity=item["severity"],
                status=item["status"],
                summary=item["summary"],
                operator_note="snapshot",
            )
            for item in snapshot.incidents
        ]


class LiveIncidentReviewProjectionProvider:
    def __init__(self, source: IncidentReviewProjectionSource) -> None:
        self._source = source

    @property
    def metadata(self) -> ProviderMetadata:
        source_metadata = getattr(self._source, "metadata", ProjectionSourceMetadata("file_projection", True, False))
        return ProviderMetadata(source_metadata.source_type, source_metadata.read_only, source_metadata.authority_coupled)

    def list_incidents(self) -> list[IncidentReviewItem]:
        snapshot = self._source.read_snapshot()
        incidents = snapshot.incidents
        replay_events = snapshot.replay_events
        mesh_snapshot = snapshot.mesh_diagnostics
        policy_impacts = snapshot.policy_impacts
        lineage = snapshot.lineage

        replay_count = {item["incident_id"]: 0 for item in incidents}
        policy_count = {item["incident_id"]: 0 for item in incidents}
        lineage_count = {item["incident_id"]: 0 for item in incidents}
        mesh_health = {item["incident_id"]: 0.0 for item in incidents}
        healing_success = {item["incident_id"]: 0.0 for item in incidents}

        for item in replay_events:
            if item["incident_id"] in replay_count:
                replay_count[item["incident_id"]] += 1
        for item in policy_impacts:
            if item["incident_id"] in policy_count:
                policy_count[item["incident_id"]] += 1
        for item in lineage:
            if item["incident_id"] in lineage_count:
                lineage_count[item["incident_id"]] += 1
        for item in mesh_snapshot:
            incident_id = item["incident_id"]
            if incident_id in mesh_health:
                mesh_health[incident_id] = float(item.get("health_score", 0.0))
                healing_success[incident_id] = float(item.get("healing_success", 0.0))

        return [
            IncidentReviewItem(
                incident_id=item["incident_id"],
                title=item["title"],
                severity=item["severity"],
                status=item["status"],
                summary=(
                    f"{item['summary']} | replay={replay_count[item['incident_id']]} "
                    f"policyImpact={policy_count[item['incident_id']]} health={mesh_health[item['incident_id']]:.2f}"
                ),
                operator_note=(
                    f"lineage={lineage_count[item['incident_id']]} healingSuccess={healing_success[item['incident_id']]:.2f}"
                ),
            )
            for item in incidents
        ]


class IncidentReviewProviderFactory:
    @staticmethod
    def build_live_default(snapshot_path: Path):
        runtime_path = Path("ledger/projections/incident_review_projection.json")
        source = RuntimeProjectionSource(runtime_projection_path=runtime_path, fallback_source=JsonFileProjectionSource(snapshot_path))
        return LiveIncidentReviewProjectionProvider(source=source)

    @staticmethod
    def build_file_backed_projection(snapshot_path: Path):
        return LiveIncidentReviewProjectionProvider(source=JsonFileProjectionSource(snapshot_path))

    @staticmethod
    def build_snapshot_for_tests(snapshot_path: Path):
        return SnapshotIncidentReviewProvider(snapshot_path=snapshot_path)
