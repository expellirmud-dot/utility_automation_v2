from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import json


@dataclass(frozen=True)
class ProjectionSnapshot:
    incidents: tuple[dict, ...]
    replay_events: tuple[dict, ...]
    mesh_diagnostics: tuple[dict, ...]
    policy_impacts: tuple[dict, ...]
    lineage: tuple[dict, ...]


@dataclass(frozen=True)
class ProjectionSourceMetadata:
    source_type: str
    read_only: bool
    authority_coupled: bool
    fallback_active: bool
    source_ref: str

    @property
    def status_label(self) -> str:
        if self.source_type == "runtime_projection" and not self.fallback_active:
            return "runtime_projection_active"
        if self.source_type == "file_projection" and self.fallback_active:
            return "file_projection_fallback"
        if self.source_type == "snapshot_test":
            return "snapshot_test_source"
        return f"{self.source_type}_active"


class IncidentReviewProjectionSource(Protocol):
    def read_snapshot(self) -> ProjectionSnapshot: ...

    def metadata(self) -> ProjectionSourceMetadata: ...


class JsonFileProjectionSource:
    def __init__(self, snapshot_path: Path, *, source_type: str = "file_projection", fallback_active: bool = False) -> None:
        self._snapshot_path = snapshot_path
        self._source_type = source_type
        self._fallback_active = fallback_active

    @staticmethod
    def _stable_sort(records: list[dict], sort_keys: tuple[str, ...]) -> tuple[dict, ...]:
        return tuple(
            sorted((dict(record) for record in records), key=lambda item: tuple(str(item.get(key, "")) for key in sort_keys))
        )

    def read_snapshot(self) -> ProjectionSnapshot:
        payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        incidents = [
            {
                "incident_id": item.get("incident_id", ""),
                "title": item.get("title", ""),
                "severity": item.get("severity", "UNKNOWN"),
                "status": item.get("status", "UNKNOWN"),
                "summary": item.get("summary", ""),
                "artifact_hash": item.get("artifact_hash", ""),
            }
            for item in payload.get("incident_explorer", [])
        ]
        replay_events = [
            {
                "incident_id": item.get("incident_id", ""),
                "event_hash": item.get("event_hash", ""),
                "causal_depth": item.get("causal_depth", 0),
                "artifact_hash": item.get("artifact_hash", ""),
            }
            for item in payload.get("replay_trace", [])
        ]
        mesh_diagnostics = [
            {
                "incident_id": item.get("incident_id", ""),
                "event_hash": item.get("event_hash", ""),
                "causal_depth": item.get("causal_depth", 0),
                "artifact_hash": item.get("artifact_hash", ""),
                "health_score": item.get("health_score", 0.0),
                "healing_success": item.get("healing_success", 0.0),
            }
            for item in payload.get("mesh_incident_viewer", [])
        ]
        policy_impacts = [
            {
                "incident_id": item.get("incident_id", ""),
                "event_hash": item.get("event_hash", ""),
                "causal_depth": item.get("causal_depth", 0),
                "artifact_hash": item.get("artifact_hash", ""),
            }
            for item in payload.get("policy_impact", [])
        ]
        lineage = [
            {
                "incident_id": item.get("incident_id", ""),
                "event_hash": item.get("event_hash", ""),
                "causal_depth": item.get("causal_depth", 0),
                "artifact_hash": item.get("artifact_hash", ""),
            }
            for item in payload.get("decision_lineage", [])
        ]
        return ProjectionSnapshot(
            incidents=self._stable_sort(incidents, ("incident_id", "artifact_hash")),
            replay_events=self._stable_sort(replay_events, ("incident_id", "event_hash", "causal_depth", "artifact_hash")),
            mesh_diagnostics=self._stable_sort(mesh_diagnostics, ("incident_id", "event_hash", "causal_depth", "artifact_hash")),
            policy_impacts=self._stable_sort(policy_impacts, ("incident_id", "event_hash", "causal_depth", "artifact_hash")),
            lineage=self._stable_sort(lineage, ("incident_id", "event_hash", "causal_depth", "artifact_hash")),
        )

    def metadata(self) -> ProjectionSourceMetadata:
        return ProjectionSourceMetadata(
            source_type=self._source_type,
            read_only=True,
            authority_coupled=False,
            fallback_active=self._fallback_active,
            source_ref=self._snapshot_path.name,
        )


class RuntimeProjectionSource(JsonFileProjectionSource):
    def __init__(self, projection_path: Path) -> None:
        super().__init__(projection_path, source_type="runtime_projection", fallback_active=False)
