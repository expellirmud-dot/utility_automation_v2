from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


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


class ProjectionFederationProviderFactory:
    @staticmethod
    def build_defaults(base_dir: Path) -> dict[str, FederationProvider]:
        return {
            "recovery": JsonArrayTelemetryProvider(
                key="recovery",
                snapshot_path=base_dir / "recovery_projection_snapshot.json",
                source_type="recovery_projection",
            ),
            "simulation": JsonArrayTelemetryProvider(
                key="simulation",
                snapshot_path=base_dir / "simulation_projection_snapshot.json",
                source_type="simulation_projection",
            ),
            "mesh": JsonArrayTelemetryProvider(
                key="mesh",
                snapshot_path=base_dir / "mesh_projection_snapshot.json",
                source_type="mesh_projection",
            ),
            "policy": JsonArrayTelemetryProvider(
                key="policy",
                snapshot_path=base_dir / "policy_projection_snapshot.json",
                source_type="policy_projection",
            ),
            "replay": JsonArrayTelemetryProvider(
                key="replay",
                snapshot_path=base_dir / "replay_projection_snapshot.json",
                source_type="replay_projection",
            ),
            "system_health": JsonArrayTelemetryProvider(
                key="system_health",
                snapshot_path=base_dir / "system_health_telemetry_snapshot.json",
                source_type="system_health_telemetry",
            ),
        }
