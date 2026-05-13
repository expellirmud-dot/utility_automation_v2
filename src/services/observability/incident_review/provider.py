from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class IncidentReviewProvider:
    """Read-only provider for deterministic incident review snapshots."""

    incidents: List[Dict[str, object]]

    def list_incidents(self) -> List[Dict[str, object]]:
        return [dict(item) for item in self.incidents]


class MockIncidentReviewProvider(IncidentReviewProvider):
    def __init__(self) -> None:
        super().__init__(
            incidents=[
                {
                    "incident_id": "INC-001",
                    "severity": "high",
                    "status": "open",
                    "summary": "Transformer drift anomaly.",
                },
                {
                    "incident_id": "INC-002",
                    "severity": "medium",
                    "status": "investigating",
                    "summary": "Telemetry lag exceeding SLA.",
                },
            ]
        )
