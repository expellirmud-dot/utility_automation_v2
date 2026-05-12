from typing import Iterable, Optional

from src.services.governance.policy_graph.policy_version import PolicySnapshot
from .candidate_comparator import CandidateComparator
from .cascading_conflict_simulator import CascadingConflictSimulator
from .governance_simulation_engine import GovernanceSimulationEngine
from .scenario_models import BatchScenarioReport, ScenarioReport
from .simulation_report import GovernanceSimulationReport


class SimulationScenarioEngine:
    def __init__(self, simulation_engine: GovernanceSimulationEngine):
        self.simulation_engine = simulation_engine
        self._cascading_simulator = CascadingConflictSimulator()
        self._candidate_comparator = CandidateComparator()

    def simulate_scenarios(
        self,
        candidates: Iterable[PolicySnapshot],
        base_version_id: Optional[str],
        actor: str,
        reason: str,
    ) -> BatchScenarioReport:
        scenario_reports = []
        canonical_candidates = sorted(
            [PolicySnapshot.from_payload(candidate.to_payload(include_hash=False)) for candidate in candidates],
            key=lambda item: item.snapshot_hash,
        )
        for candidate in canonical_candidates:
            base_report = self.simulation_engine.simulate_policy_change(
                candidate_snapshot=candidate,
                base_version_id=base_version_id,
            )
            cascade_conflicts = self._cascading_simulator.detect(candidate)
            combined_conflicts = tuple(sorted(base_report.conflict_findings + cascade_conflicts, key=lambda c: (c.conflict_type, c.rule_a, c.rule_b, c.severity)))
            recommendation = self.simulation_engine._recommend(base_report.risk_findings, combined_conflicts, base_report.target_stage)
            merged_report = GovernanceSimulationReport(
                base_version_id=base_report.base_version_id,
                target_stage=base_report.target_stage,
                candidate_snapshot_hash=base_report.candidate_snapshot_hash,
                diff_changes=base_report.diff_changes,
                risk_findings=base_report.risk_findings,
                conflict_findings=combined_conflicts,
                recommendation=recommendation,
                evidence_hashes=base_report.evidence_hashes,
                ai_advice=base_report.ai_advice,
            )
            scenario_reports.append(ScenarioReport(
                candidate_snapshot=candidate,
                simulation_report=merged_report,
                actor=actor,
                reason=reason,
            ))

        scenarios = tuple(scenario_reports)
        comparisons = self._candidate_comparator.compare(scenarios)
        return BatchScenarioReport(
            base_version_id=base_version_id,
            actor=actor,
            reason=reason,
            scenario_reports=scenarios,
            candidate_comparisons=comparisons,
        )
