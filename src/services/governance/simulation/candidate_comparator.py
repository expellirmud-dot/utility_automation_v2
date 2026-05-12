from typing import Iterable, Tuple

from .scenario_models import CandidateComparison, ScenarioReport


class CandidateComparator:
    def compare(self, scenario_reports: Iterable[ScenarioReport]) -> Tuple[CandidateComparison, ...]:
        comparisons = []
        for report in scenario_reports:
            comparisons.append(CandidateComparison(
                candidate_snapshot_hash=report.candidate_snapshot_hash,
                scenario_hash=report.scenario_hash,
                recommendation=report.simulation_report.recommendation,
                risk_count=len(report.simulation_report.risk_findings),
                conflict_count=len(report.simulation_report.conflict_findings),
            ))
        return tuple(sorted(comparisons, key=lambda item: item.rank_key))
