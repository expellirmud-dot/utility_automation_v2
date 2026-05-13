from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import json

from .incident_review_models import IncidentReviewItem


@dataclass(frozen=True)
class ProjectionSnapshot:
    incidents: tuple[dict, ...]
    replay_events: tuple[dict, ...]
    mesh_diagnostics: tuple[dict, ...]
    policy_impacts: tuple[dict, ...]
    lineage: tuple[dict, ...]


class IncidentProjectionProvider(Protocol):
    def read_incidents(self) -> tuple[dict, ...]: ...


class ReplayProjectionProvider(Protocol):
    def read_replay_events(self) -> tuple[dict, ...]: ...


class MeshDiagnosticsProjectionProvider(Protocol):
    def read_mesh_snapshot(self) -> tuple[dict, ...]: ...


class PolicyImpactProjectionProvider(Protocol):
    def read_policy_impacts(self) -> tuple[dict, ...]: ...


class LineageProjectionProvider(Protocol):
    def read_lineage(self) -> tuple[dict, ...]: ...


class JsonSnapshotProjectionProvider(
    IncidentProjectionProvider,
    ReplayProjectionProvider,
    MeshDiagnosticsProjectionProvider,
    PolicyImpactProjectionProvider,
    LineageProjectionProvider,
):
    def __init__(self, snapshot_path: Path) -> None:
        self._snapshot_path = snapshot_path

    @staticmethod
    def _stable_sort(records: list[dict], sort_keys: tuple[str, ...]) -> tuple[dict, ...]:
        def stable_key(item: dict) -> tuple[str, ...]:
            return tuple(str(item.get(key, "")) for key in sort_keys)

        normalized = [dict(record) for record in records]
        return tuple(sorted(normalized, key=stable_key))

    def _load(self) -> ProjectionSnapshot:
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

    def read_incidents(self) -> tuple[dict, ...]:
        return self._load().incidents

    def read_replay_events(self) -> tuple[dict, ...]:
        return self._load().replay_events

    def read_mesh_snapshot(self) -> tuple[dict, ...]:
        return self._load().mesh_diagnostics

    def read_policy_impacts(self) -> tuple[dict, ...]:
        return self._load().policy_impacts

    def read_lineage(self) -> tuple[dict, ...]:
        return self._load().lineage


class LiveIncidentReviewProjectionProvider:
    def __init__(
        self,
        incident_provider: IncidentProjectionProvider,
        replay_provider: ReplayProjectionProvider,
        mesh_provider: MeshDiagnosticsProjectionProvider,
        policy_provider: PolicyImpactProjectionProvider,
        lineage_provider: LineageProjectionProvider,
    ) -> None:
        self._incident_provider = incident_provider
        self._replay_provider = replay_provider
        self._mesh_provider = mesh_provider
        self._policy_provider = policy_provider
        self._lineage_provider = lineage_provider

    def list_incidents(self) -> list[IncidentReviewItem]:
        incidents = self._incident_provider.read_incidents()
        replay_events = self._replay_provider.read_replay_events()
        mesh_snapshot = self._mesh_provider.read_mesh_snapshot()
        policy_impacts = self._policy_provider.read_policy_impacts()
        lineage = self._lineage_provider.read_lineage()

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
