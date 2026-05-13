from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from src.ui.incident_review.incident_review_service import IncidentReviewService
from src.ui.incident_review.projection_providers import IncidentReviewProviderFactory
from src.ui.projection_federation_providers import FederationProvider, ProjectionFederationProviderFactory


@dataclass(frozen=True)
class ProjectionProviderStatus:
    key: str
    status: str
    label: str
    source_ref: str
    provider_kind: str
    connected: bool
    stale: bool


@dataclass(frozen=True)
class ProjectionSummaryCard:
    key: str
    title: str
    domain: str
    status: str
    label: str
    provider_status: ProjectionProviderStatus
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

    def __init__(self, incident_service: IncidentReviewService, providers: dict[str, FederationProvider]) -> None:
        self._incident_service = incident_service
        self._providers = providers

    @classmethod
    def build_default(cls) -> "ProjectionFederationService":
        incident_service = IncidentReviewService(
            provider=IncidentReviewProviderFactory.build_live_default(
                Path(__file__).resolve().parent / "incident_review" / "projection_snapshot.json"
            )
        )
        providers = ProjectionFederationProviderFactory.build_defaults(Path(__file__).resolve().parent)
        return cls(incident_service=incident_service, providers=providers)

    def report(self) -> ProjectionFederationReport:
        cards = []
        for key, title, domain, stable_order in self._ORDER:
            if key == "incident_review":
                cards.append(self._build_incident_card(title=title, domain=domain, stable_order=stable_order))
            else:
                cards.append(self._build_domain_card(key=key, title=title, domain=domain, stable_order=stable_order))
        ordered = tuple(sorted(cards, key=lambda item: item.stable_order))
        return ProjectionFederationReport(cards=ordered)

    def _build_incident_card(self, *, title: str, domain: str, stable_order: int) -> ProjectionSummaryCard:
        metadata = self._incident_service.source_metadata()
        incidents = self._incident_service.list_incidents()
        status = ProjectionProviderStatus(
            key="incident_review",
            status="connected" if not metadata.fallback_active else "not_connected",
            label=metadata.status_label,
            source_ref=metadata.source_type,
            provider_kind="incident_review_provider",
            connected=not metadata.fallback_active,
            stale=metadata.fallback_active,
        )
        return ProjectionSummaryCard(
            key=status.key,
            title=title,
            domain=domain,
            status=status.status,
            label=status.label,
            provider_status=status,
            read_only=metadata.read_only,
            authority_coupled=metadata.authority_coupled,
            source_type=metadata.source_type,
            fallback_active=metadata.fallback_active,
            item_count=len(incidents),
            stable_order=stable_order,
        )

    def _build_domain_card(self, *, key: str, title: str, domain: str, stable_order: int) -> ProjectionSummaryCard:
        provider = self._providers[key]
        metadata = provider.read_metadata()
        provider_status = ProjectionProviderStatus(
            key=key,
            status=metadata.status,
            label=metadata.label,
            source_ref=metadata.source_type,
            provider_kind=provider.__class__.__name__,
            connected=metadata.status == "connected",
            stale=metadata.fallback_active or metadata.status in {"degraded", "not_connected"},
        )
        return ProjectionSummaryCard(
            key=key,
            title=title,
            domain=domain,
            status=metadata.status,
            label=metadata.label,
            provider_status=provider_status,
            read_only=True,
            authority_coupled=False,
            source_type=metadata.source_type,
            fallback_active=metadata.fallback_active,
            item_count=metadata.item_count,
            stable_order=stable_order,
        )


def card_to_dict(card: ProjectionSummaryCard) -> dict[str, object]:
    return asdict(card)
