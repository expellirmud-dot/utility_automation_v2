from __future__ import annotations

from typing import Protocol

from .incident_review_models import IncidentReviewItem
from .mock_data import MOCK_INCIDENTS


class IncidentReviewProvider(Protocol):
    def list_incidents(self) -> list[IncidentReviewItem]:
        """Return incident records in deterministic provider order."""


class MockIncidentReviewProvider:
    def list_incidents(self) -> list[IncidentReviewItem]:
        return list(MOCK_INCIDENTS)


class IncidentReviewService:
    def __init__(self, provider: IncidentReviewProvider) -> None:
        self._provider = provider

    def list_incidents(self) -> list[IncidentReviewItem]:
        # Deterministic ordering from provider insertion order only.
        return self._provider.list_incidents()
