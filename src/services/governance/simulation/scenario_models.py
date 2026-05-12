from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

from src.services.governance.policy_graph.policy_version import PolicySnapshot, canonicalize, stable_hash
from .simulation_report import GovernanceSimulationReport


RANKING_PRECEDENCE = (
    "block_until_fixed",
    "manual_review",
    "quorum_required",
    "allow_simulation",
)


@dataclass(frozen=True)
class CandidateComparison:
    candidate_snapshot_hash: str
    scenario_hash: str
    recommendation: str
    risk_count: int
    conflict_count: int
    rank_key: Tuple[int, int, int, str] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, "rank_key", self._build_rank_key())

    def _build_rank_key(self) -> Tuple[int, int, int, str]:
        recommendation_rank = RANKING_PRECEDENCE.index(self.recommendation)
        return (recommendation_rank, -self.risk_count, -self.conflict_count, self.candidate_snapshot_hash)

    def to_payload(self) -> dict:
        return canonicalize({
            "candidate_snapshot_hash": self.candidate_snapshot_hash,
            "scenario_hash": self.scenario_hash,
            "recommendation": self.recommendation,
            "risk_count": self.risk_count,
            "conflict_count": self.conflict_count,
            "rank_key": list(self.rank_key),
        })


@dataclass(frozen=True)
class ScenarioReport:
    candidate_snapshot: PolicySnapshot
    simulation_report: GovernanceSimulationReport
    actor: str
    reason: str
    scenario_hash: str = ""

    def __post_init__(self):
        if not self.scenario_hash:
            object.__setattr__(self, "scenario_hash", stable_hash(self.to_payload(include_hash=False)))

    @property
    def candidate_snapshot_hash(self) -> str:
        return self.candidate_snapshot.snapshot_hash

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "candidate_snapshot": self.candidate_snapshot.to_payload(include_hash=True),
            "simulation_report": self.simulation_report.to_payload(include_hash=True, include_ai=True),
            "actor": self.actor,
            "reason": self.reason,
        }
        if include_hash:
            payload["scenario_hash"] = self.scenario_hash
        return canonicalize(payload)


@dataclass(frozen=True)
class BatchScenarioReport:
    base_version_id: Optional[str]
    actor: str
    reason: str
    scenario_reports: Tuple[ScenarioReport, ...]
    candidate_comparisons: Tuple[CandidateComparison, ...]
    batch_hash: str = ""

    def __post_init__(self):
        object.__setattr__(self, "scenario_reports", tuple(sorted(self.scenario_reports, key=lambda r: r.candidate_snapshot_hash)))
        object.__setattr__(self, "candidate_comparisons", tuple(sorted(self.candidate_comparisons, key=lambda c: c.rank_key)))
        if not self.batch_hash:
            object.__setattr__(self, "batch_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "base_version_id": self.base_version_id,
            "actor": self.actor,
            "reason": self.reason,
            "scenario_reports": [item.to_payload(include_hash=True) for item in self.scenario_reports],
            "candidate_comparisons": [item.to_payload() for item in self.candidate_comparisons],
        }
        if include_hash:
            payload["batch_hash"] = self.batch_hash
        return canonicalize(payload)
