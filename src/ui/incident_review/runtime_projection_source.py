from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .projection_source import IncidentReviewProjectionSource, JsonFileProjectionSource, ProjectionSnapshot


@dataclass(frozen=True)
class ProjectionSourceMetadata:
    source_type: str
    read_only: bool
    authority_coupled: bool


class RuntimeProjectionSource:
    """Read-only runtime projection source with explicit file-backed fallback."""

    def __init__(self, runtime_projection_path: Path, fallback_source: IncidentReviewProjectionSource) -> None:
        self._runtime_projection_path = runtime_projection_path
        self._runtime_source = JsonFileProjectionSource(runtime_projection_path)
        self._fallback_source = fallback_source

    @property
    def metadata(self) -> ProjectionSourceMetadata:
        if self._runtime_projection_path.exists():
            return ProjectionSourceMetadata("runtime_projection", True, False)
        return ProjectionSourceMetadata("file_projection", True, False)

    def read_snapshot(self) -> ProjectionSnapshot:
        if self._runtime_projection_path.exists():
            return self._runtime_source.read_snapshot()
        return self._fallback_source.read_snapshot()
