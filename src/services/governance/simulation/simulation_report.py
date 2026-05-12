from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from src.services.governance.policy_graph.policy_diff_engine import PolicyDiffChange
from src.services.governance.policy_graph.policy_version import canonicalize, stable_hash


RECOMMENDATION_PRECEDENCE = (
    "allow_simulation",
    "quorum_required",
    "manual_review",
    "block_until_fixed",
)


@dataclass(frozen=True)
class RiskFinding:
    section: str
    path: str
    severity: str
    code: str
    message: str
    before: Any = None
    after: Any = None

    def to_payload(self) -> dict:
        return canonicalize({
            "section": self.section,
            "path": self.path,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "before": self.before,
            "after": self.after,
        })


@dataclass(frozen=True)
class ConflictFinding:
    conflict_type: str
    rule_a: str
    rule_b: str
    severity: str = "BLOCKER"

    def to_payload(self) -> dict:
        return canonicalize({
            "conflict_type": self.conflict_type,
            "rule_a": self.rule_a,
            "rule_b": self.rule_b,
            "severity": self.severity,
        })


@dataclass(frozen=True)
class AIAdvice:
    warnings: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    manual_review_suggested: bool = False

    def __post_init__(self):
        object.__setattr__(self, "warnings", tuple(sorted(self.warnings)))
        object.__setattr__(self, "notes", tuple(sorted(self.notes)))

    def to_payload(self) -> dict:
        return {
            "warnings": list(self.warnings),
            "notes": list(self.notes),
            "manual_review_suggested": self.manual_review_suggested,
        }


@dataclass(frozen=True)
class GovernanceSimulationReport:
    base_version_id: Optional[str]
    target_stage: str
    candidate_snapshot_hash: str
    diff_changes: Tuple[PolicyDiffChange, ...]
    risk_findings: Tuple[RiskFinding, ...]
    conflict_findings: Tuple[ConflictFinding, ...]
    recommendation: str
    evidence_hashes: Tuple[str, ...]
    ai_advice: Optional[AIAdvice] = None
    simulation_hash: str = field(default="")

    def __post_init__(self):
        if self.recommendation not in RECOMMENDATION_PRECEDENCE:
            raise ValueError(f"Unsupported recommendation: {self.recommendation}")
        object.__setattr__(
            self,
            "diff_changes",
            tuple(sorted(self.diff_changes, key=lambda c: (c.section, c.path, c.operation))),
        )
        object.__setattr__(
            self,
            "risk_findings",
            tuple(sorted(self.risk_findings, key=lambda r: (r.section, r.path, r.code, r.severity))),
        )
        object.__setattr__(
            self,
            "conflict_findings",
            tuple(sorted(self.conflict_findings, key=lambda c: (c.conflict_type, c.rule_a, c.rule_b))),
        )
        object.__setattr__(self, "evidence_hashes", tuple(sorted(self.evidence_hashes)))
        if not self.simulation_hash:
            object.__setattr__(self, "simulation_hash", stable_hash(self.to_payload(include_hash=False, include_ai=False)))

    def to_payload(self, include_hash: bool = True, include_ai: bool = True) -> dict:
        payload = {
            "base_version_id": self.base_version_id,
            "target_stage": self.target_stage,
            "candidate_snapshot_hash": self.candidate_snapshot_hash,
            "diff_changes": [self._diff_to_payload(change) for change in self.diff_changes],
            "risk_findings": [finding.to_payload() for finding in self.risk_findings],
            "conflict_findings": [finding.to_payload() for finding in self.conflict_findings],
            "recommendation": self.recommendation,
            "evidence_hashes": list(self.evidence_hashes),
        }
        if include_ai:
            payload["ai_advice"] = self.ai_advice.to_payload() if self.ai_advice else None
        if include_hash:
            payload["simulation_hash"] = self.simulation_hash
        return canonicalize(payload)

    def _diff_to_payload(self, change: PolicyDiffChange) -> dict:
        return canonicalize({
            "section": change.section,
            "path": change.path,
            "operation": change.operation,
            "before": change.before,
            "after": change.after,
        })
