from __future__ import annotations

from typing import Dict, List

from src.services.observability.incident_review.provider import IncidentReviewProvider


class IncidentReviewService:
    """Read-only incident review orchestration service."""

    def __init__(self, provider: IncidentReviewProvider) -> None:
        self._provider = provider

    def get_incidents(self) -> List[Dict[str, object]]:
        return self._provider.list_incidents()

    def get_incident(self, incident_id: str) -> Dict[str, object] | None:
        for incident in self._provider.list_incidents():
            if incident.get("incident_id") == incident_id:
                return incident
        return None

    def get_analytics(self) -> Dict[str, object]:
        incidents = self._provider.list_incidents()
        counts: Dict[str, int] = {}
        for item in incidents:
            sev = str(item.get("severity", "unknown"))
            counts[sev] = counts.get(sev, 0) + 1
        return {
            "total_incidents": len(incidents),
            "severity_counts": dict(sorted(counts.items())),
        }
