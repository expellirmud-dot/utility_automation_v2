from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from src.ui.incident_review.incident_review_service import IncidentReviewService
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory


@dataclass(frozen=True)
class ProjectionProviderStatus:
    key: str
    status: str
    label: str


@dataclass(frozen=True)
class ProjectionSummaryCard:
    key: str
    title: str
    domain: str
    status: str
    label: str
    read_only: bool
    authority_coupled: bool
    source_type: str
    fallback_active: bool
    item_count: int
    stable_order: int


@dataclass(frozen=True)
class ProjectionFederationReport:
    cards: tuple[ProjectionSummaryCard, ...]


class ProjectionFederationService:
    _ORDER = (
        ("incident_review", "Incident Review", "incident", 10),
        ("recovery", "Recovery", "recovery", 20),
        ("simulation", "Simulation", "simulation", 30),
        ("mesh", "Mesh", "mesh", 40),
        ("policy", "Policy", "policy", 50),
        ("replay", "Replay", "replay", 60),
        ("system_health", "System Health", "system_health", 70),
    )

    def __init__(self, incident_service: IncidentReviewService) -> None:
        self._incident_service = incident_service

    @classmethod
    def build_default(cls) -> "ProjectionFederationService":
        incident_service = IncidentReviewService(
            provider=IncidentReviewProviderFactory.build_live_default(
                Path(__file__).resolve().parent / "incident_review" / "projection_snapshot.json"
            )
        )
        return cls(incident_service=incident_service)

    def report(self) -> ProjectionFederationReport:
        cards = []
        for key, title, domain, stable_order in self._ORDER:
            if key == "incident_review":
                cards.append(self._build_incident_card(title=title, domain=domain, stable_order=stable_order))
            else:
                cards.append(self._placeholder_card(key=key, title=title, domain=domain, stable_order=stable_order))
        ordered = tuple(sorted(cards, key=lambda item: item.stable_order))
        return ProjectionFederationReport(cards=ordered)

    def _build_incident_card(self, *, title: str, domain: str, stable_order: int) -> ProjectionSummaryCard:
        metadata = self._incident_service.source_metadata()
        incidents = self._incident_service.list_incidents()
        status = ProjectionProviderStatus(key="incident_review", status="connected", label=metadata.status_label)
        return ProjectionSummaryCard(
            key=status.key,
            title=title,
            domain=domain,
            status=status.status,
            label=status.label,
            read_only=metadata.read_only,
            authority_coupled=metadata.authority_coupled,
            source_type=metadata.source_type,
            fallback_active=metadata.fallback_active,
            item_count=len(incidents),
            stable_order=stable_order,
        )

    @staticmethod
    def _placeholder_card(*, key: str, title: str, domain: str, stable_order: int) -> ProjectionSummaryCard:
        status = ProjectionProviderStatus(key=key, status="not_connected", label="Not connected")
        return ProjectionSummaryCard(
            key=status.key,
            title=title,
            domain=domain,
            status=status.status,
            label=status.label,
            read_only=True,
            authority_coupled=False,
            source_type="not_connected",
            fallback_active=True,
            item_count=0,
            stable_order=stable_order,
        )


def card_to_dict(card: ProjectionSummaryCard) -> dict[str, object]:
    return asdict(card)
