from __future__ import annotations

from typing import Protocol

from .incident_review_models import IncidentReviewItem


class IncidentReviewProvider(Protocol):
    def list_incidents(self) -> list[IncidentReviewItem]:
        """Return incident records in deterministic provider order."""

    def source_metadata(self):
        """Return read-only projection source metadata."""


class IncidentReviewService:
    def __init__(self, provider: IncidentReviewProvider) -> None:
        self._provider = provider

    def list_incidents(self) -> list[IncidentReviewItem]:
        return self._provider.list_incidents()

    def source_metadata(self):
        return self._provider.source_metadata()
