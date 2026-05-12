from dataclasses import replace
from typing import Iterable, Optional, Tuple

from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.governance.policy_graph.policy_diff_engine import PolicyDiffEngine
from src.services.governance.policy_graph.policy_graph_engine import PolicyGraphEngine
from src.services.governance.policy_graph.policy_version import PolicySnapshot
from .conflict_predictor import PolicyConflictPredictor
from .risk_analyzer import GovernanceRiskAnalyzer
from .simulation_report import GovernanceSimulationReport, RiskFinding


class GovernanceSimulationEngine:
    STAGE_TRANSITIONS = {
        "draft": "simulation",
        "simulation": "approved",
        "approved": "production",
    }
    RECOMMENDATION_ORDER = {
        "allow_simulation": 0,
        "quorum_required": 1,
        "manual_review": 2,
        "block_until_fixed": 3,
    }

    def __init__(
        self,
        events: Optional[Iterable[CanonicalEvent]] = None,
        graph_engine: Optional[PolicyGraphEngine] = None,
        ai_advisor=None,
    ):
        if events is None and graph_engine is not None:
            events = graph_engine.transition_events
        self.events: Tuple[CanonicalEvent, ...] = tuple(events or ())
        self.ai_advisor = ai_advisor

    def simulate_policy_change(
        self,
        candidate_snapshot: PolicySnapshot,
        base_version_id: Optional[str] = None,
        target_stage: str = "simulation",
    ) -> GovernanceSimulationReport:
        graph = self._rebuild_graph()
        base_version = graph.get_version(base_version_id) if base_version_id else graph.get_production_head() or graph.current_head()
        base_snapshot = base_version.snapshot if base_version else PolicySnapshot()
        canonical_candidate = self._canonical_snapshot(candidate_snapshot)

        diff_changes = PolicyDiffEngine(None).diff_snapshots(base_snapshot, canonical_candidate)
        risk_findings = GovernanceRiskAnalyzer().analyze(diff_changes)
        conflict_findings = PolicyConflictPredictor().detect(canonical_candidate)
        recommendation = self._recommend(risk_findings, conflict_findings, target_stage)

        report = GovernanceSimulationReport(
            base_version_id=base_version.version_id if base_version else None,
            target_stage=target_stage,
            candidate_snapshot_hash=canonical_candidate.snapshot_hash,
            diff_changes=diff_changes,
            risk_findings=risk_findings,
            conflict_findings=conflict_findings,
            recommendation=recommendation,
            evidence_hashes=self._evidence_hashes(),
        )
        return self._attach_ai_advice(report)

    def preflight_promotion(
        self,
        version_id: str,
        target_stage: str,
    ) -> GovernanceSimulationReport:
        graph = self._rebuild_graph()
        version = graph.get_version(version_id)
        extra_risks = self._promotion_risks(version.stage, target_stage)
        report = self.simulate_policy_change(
            candidate_snapshot=version.snapshot,
            base_version_id=version_id,
            target_stage=target_stage,
        )
        if not extra_risks:
            return report

        risks = tuple(sorted(report.risk_findings + extra_risks, key=lambda r: (r.section, r.path, r.code, r.severity)))
        recommendation = self._recommend(risks, report.conflict_findings, target_stage)
        deterministic_report = replace(
            report,
            risk_findings=risks,
            recommendation=recommendation,
            ai_advice=None,
            simulation_hash="",
        )
        return self._attach_ai_advice(deterministic_report)

    def _rebuild_graph(self) -> PolicyGraphEngine:
        return PolicyGraphEngine.rebuild_from_ledger(self.events)

    def _canonical_snapshot(self, snapshot: PolicySnapshot) -> PolicySnapshot:
        return PolicySnapshot.from_payload(snapshot.to_payload(include_hash=False))

    def _evidence_hashes(self) -> Tuple[str, ...]:
        return tuple(
            sorted(event.global_chain_hash for event in self.events if event.global_chain_hash)
        )

    def _recommend(self, risks, conflicts, target_stage: str) -> str:
        recommendations = ["allow_simulation"]
        if target_stage in {"approved", "production"}:
            recommendations.append("quorum_required")
        if any(finding.severity in {"HIGH", "MEDIUM"} for finding in risks):
            recommendations.append("manual_review")
        if conflicts or any(finding.severity == "BLOCKER" for finding in risks):
            recommendations.append("block_until_fixed")
        return max(recommendations, key=lambda item: self.RECOMMENDATION_ORDER[item])

    def _promotion_risks(self, current_stage: str, target_stage: str) -> Tuple[RiskFinding, ...]:
        expected = self.STAGE_TRANSITIONS.get(current_stage)
        if expected == target_stage:
            return ()
        return (RiskFinding(
            section="promotion",
            path=f"{current_stage}->{target_stage}",
            severity="BLOCKER",
            code="INVALID_PROMOTION_TRANSITION",
            message="Promotion preflight detected a non-sequential stage transition.",
            before=current_stage,
            after=target_stage,
        ),)

    def _attach_ai_advice(self, report: GovernanceSimulationReport) -> GovernanceSimulationReport:
        if not self.ai_advisor:
            return report
        advice = self.ai_advisor.advise(report.to_payload(include_hash=True, include_ai=False))
        return replace(report, ai_advice=advice)
