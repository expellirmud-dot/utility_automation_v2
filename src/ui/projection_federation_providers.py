from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from src.services.governance.simulation import simulation_api


@dataclass(frozen=True)
class FederationReadMetadata:
    label: str
    status: str
    source_type: str
    fallback_active: bool
    item_count: int


class FederationProvider:
    key: str

    def read_metadata(self) -> FederationReadMetadata:
        raise NotImplementedError


class JsonArrayTelemetryProvider(FederationProvider):
    def __init__(self, *, key: str, snapshot_path: Path, source_type: str) -> None:
        self.key = key
        self._snapshot_path = snapshot_path
        self._source_type = source_type

    def read_metadata(self) -> FederationReadMetadata:
        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
            items = payload.get("items", []) if isinstance(payload, dict) else []
            item_count = len(items) if isinstance(items, list) else 0
            return FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type=self._source_type,
                fallback_active=False,
                item_count=item_count,
            )
        except (OSError, ValueError, TypeError, AttributeError):
            return FederationReadMetadata(
                label="Deterministic fallback",
                status="not_connected",
                source_type="deterministic_fallback",
                fallback_active=True,
                item_count=0,
            )


class SnapshotReadModelProvider(FederationProvider):
    def __init__(self, *, key: str, snapshot_path: Path, source_type: str, degraded_label: str) -> None:
        self.key = key
        self._snapshot_path = snapshot_path
        self._source_type = source_type
        self._degraded_label = degraded_label

    def read_metadata(self) -> FederationReadMetadata:
        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
            items = payload.get("items", []) if isinstance(payload, dict) else []
            item_count = len(items) if isinstance(items, list) else 0
            return FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type=self._source_type,
                fallback_active=False,
                item_count=item_count,
            )
        except (OSError, ValueError, TypeError, AttributeError):
            return FederationReadMetadata(
                label=self._degraded_label,
                status="degraded",
                source_type="deterministic_fallback",
                fallback_active=True,
                item_count=0,
            )


class RecoveryReadModelProvider(SnapshotReadModelProvider):
    def __init__(self, *, key: str, snapshot_path: Path) -> None:
        super().__init__(
            key=key,
            snapshot_path=snapshot_path,
            source_type="recovery_read_model",
            degraded_label="Recovery read-model unavailable",
        )


class SimulationReadModelProvider(FederationProvider):
    def __init__(self, *, key: str) -> None:
        self.key = key

    def read_metadata(self) -> FederationReadMetadata:
        reports = simulation_api._simulation_reports
        if isinstance(reports, dict):
            return FederationReadMetadata(
                label="Connected",
                status="connected",
                source_type="simulation_read_model",
                fallback_active=False,
                item_count=len(reports),
            )
        return FederationReadMetadata(
            label="Simulation read-model unavailable",
            status="degraded",
            source_type="deterministic_fallback",
            fallback_active=True,
            item_count=0,
        )


class SystemHealthReadModelProvider(SnapshotReadModelProvider):
    def __init__(self, *, key: str, snapshot_path: Path) -> None:
        super().__init__(
            key=key,
            snapshot_path=snapshot_path,
            source_type="system_health_read_model",
            degraded_label="System health read-model unavailable",
        )


class ProjectionFederationProviderFactory:
    @staticmethod
    def build_defaults(base_dir: Path) -> dict[str, FederationProvider]:
        return {
            "recovery": RecoveryReadModelProvider(
                key="recovery",
                snapshot_path=base_dir / "recovery_projection_snapshot.json",
            ),
            "simulation": SimulationReadModelProvider(key="simulation"),
            "mesh": SnapshotReadModelProvider(
                key="mesh",
                snapshot_path=base_dir / "mesh_projection_snapshot.json",
                source_type="mesh_read_model",
                degraded_label="Mesh read-model unavailable",
            ),
            "policy": SnapshotReadModelProvider(
                key="policy",
                snapshot_path=base_dir / "policy_projection_snapshot.json",
                source_type="policy_read_model",
                degraded_label="Policy read-model unavailable",
            ),
            "replay": SnapshotReadModelProvider(
                key="replay",
                snapshot_path=base_dir / "replay_projection_snapshot.json",
                source_type="replay_read_model",
                degraded_label="Replay read-model unavailable",
            ),
            "system_health": SystemHealthReadModelProvider(
                key="system_health",
                snapshot_path=base_dir / "system_health_telemetry_snapshot.json",
            ),
        }
