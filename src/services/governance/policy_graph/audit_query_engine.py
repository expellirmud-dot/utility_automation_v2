from typing import Iterable, Optional

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .governance_explanation_engine import GovernanceExplanationEngine
from .lineage_explainer import LineageExplainer
from .policy_diff_engine import PolicyDiffEngine
from .policy_graph_engine import PolicyGraphEngine
from .temporal_reconstructor import TemporalReconstructor


class AuditQueryEngine:
    def __init__(self, events: Optional[Iterable[CanonicalEvent]] = None, graph_engine: Optional[PolicyGraphEngine] = None):
        if events is None and graph_engine is not None:
            events = graph_engine.transition_events
        self.reconstructor = TemporalReconstructor(events or [])
        self.events = self.reconstructor.events

    def policy_at_timestamp(self, timestamp):
        return TemporalReconstructor(self.events).policy_at_timestamp(timestamp)

    def policy_at_version(self, version_id: str):
        return TemporalReconstructor(self.events).policy_at_version(version_id)

    def diff_versions(self, from_version_id: str, to_version_id: str):
        graph = TemporalReconstructor(self.events).rebuild_graph()
        return PolicyDiffEngine(graph).diff(from_version_id, to_version_id)

    def production_diff(self, from_version_id: str, to_version_id: str):
        graph = TemporalReconstructor(self.events).rebuild_graph()
        from_version = graph.get_version(from_version_id)
        to_version = graph.get_version(to_version_id)
        if from_version.stage != "production" or to_version.stage != "production":
            raise ValueError("production_diff requires both versions to be production")
        return PolicyDiffEngine(graph).diff(from_version_id, to_version_id)

    def rollback_impact_diff(self, rollback_version_id: str):
        graph = TemporalReconstructor(self.events).rebuild_graph()
        rollback_version = graph.get_version(rollback_version_id)
        if not rollback_version.rollback_target_id:
            raise ValueError("rollback_impact_diff requires a rollback version")
        if not rollback_version.parent_version_ids:
            raise ValueError("Rollback version has no parent impact source")
        return PolicyDiffEngine(graph).diff(rollback_version.parent_version_ids[0], rollback_version_id)

    def explain_version(self, version_id: str):
        return GovernanceExplanationEngine(self.events).explain_version(version_id)

    def ancestors(self, version_id: str):
        return LineageExplainer(self.events).ancestors(version_id)

    def descendants(self, version_id: str):
        return LineageExplainer(self.events).descendants(version_id)

    def rollback_ancestry(self, version_id: str):
        return LineageExplainer(self.events).rollback_ancestry(version_id)

    def promotion_lineage(self, version_id: str):
        return LineageExplainer(self.events).promotion_lineage(version_id)
