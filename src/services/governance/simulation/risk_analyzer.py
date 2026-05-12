from typing import Iterable, Tuple

from src.services.governance.policy_graph.policy_diff_engine import PolicyDiffChange
from .simulation_report import RiskFinding


class GovernanceRiskAnalyzer:
    def analyze(self, changes: Iterable[PolicyDiffChange]) -> Tuple[RiskFinding, ...]:
        findings = []
        for change in changes:
            finding = self._finding_for_change(change)
            if finding:
                findings.append(finding)
        return tuple(sorted(findings, key=lambda r: (r.section, r.path, r.code, r.severity)))

    def _finding_for_change(self, change: PolicyDiffChange):
        if change.section == "thresholds":
            return RiskFinding(
                section=change.section,
                path=change.path,
                severity="HIGH",
                code="RISKY_THRESHOLD_CHANGE",
                message="Policy threshold changed and requires review before promotion.",
                before=change.before,
                after=change.after,
            )

        if change.section == "permissions":
            severity = "HIGH" if change.operation in {"added", "changed"} else "MEDIUM"
            return RiskFinding(
                section=change.section,
                path=change.path,
                severity=severity,
                code="PERMISSION_CHANGE",
                message="Policy permissions changed and may alter governance access.",
                before=change.before,
                after=change.after,
            )

        if change.section == "governance_constraints":
            if self._weakens_constraint(change):
                return RiskFinding(
                    section=change.section,
                    path=change.path,
                    severity="BLOCKER",
                    code="GOVERNANCE_CONSTRAINT_WEAKENED",
                    message="Governance constraint appears weakened and must be fixed before promotion.",
                    before=change.before,
                    after=change.after,
                )
            return RiskFinding(
                section=change.section,
                path=change.path,
                severity="HIGH",
                code="GOVERNANCE_CONSTRAINT_CHANGE",
                message="Governance constraint changed and requires manual review.",
                before=change.before,
                after=change.after,
            )

        return None

    def _weakens_constraint(self, change: PolicyDiffChange) -> bool:
        if change.operation == "removed":
            return True
        if isinstance(change.before, bool) and change.before is True and change.after is False:
            return True
        if isinstance(change.before, (int, float)) and isinstance(change.after, (int, float)):
            return change.after < change.before
        return False
