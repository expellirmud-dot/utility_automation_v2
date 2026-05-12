from typing import Dict, List, Mapping, Tuple

from src.services.governance.policy_graph.policy_version import PolicySnapshot
from .simulation_report import ConflictFinding


class CascadingConflictSimulator:
    def detect(self, snapshot: PolicySnapshot) -> Tuple[ConflictFinding, ...]:
        findings: List[ConflictFinding] = []
        findings.extend(self._threshold_interaction_failures(snapshot))
        findings.extend(self._permission_escalation_cascades(snapshot))
        findings.extend(self._governance_constraint_weakening_chains(snapshot))
        findings.extend(self._rule_dependency_conflicts(snapshot))
        return tuple(sorted(findings, key=lambda c: (c.conflict_type, c.rule_a, c.rule_b, c.severity)))

    def _threshold_interaction_failures(self, snapshot: PolicySnapshot) -> List[ConflictFinding]:
        thresholds: Dict[str, int] = {str(k): int(v) for k, v in snapshot.thresholds.items() if isinstance(v, (int, float))}
        if "approval" in thresholds and "emergency" in thresholds and thresholds["emergency"] > thresholds["approval"]:
            return [ConflictFinding("THRESHOLD_INTERACTION_FAILURE", "emergency", "approval", "BLOCKER")]
        return []

    def _permission_escalation_cascades(self, snapshot: PolicySnapshot) -> List[ConflictFinding]:
        approve_roles = set(snapshot.permissions.get("approve", ()))
        promote_roles = set(snapshot.permissions.get("promote", ()))
        if promote_roles and promote_roles.issubset(approve_roles):
            return [ConflictFinding("PERMISSION_ESCALATION_CASCADE", "approve", "promote", "BLOCKER")]
        return []

    def _governance_constraint_weakening_chains(self, snapshot: PolicySnapshot) -> List[ConflictFinding]:
        quorum_required = bool(snapshot.governance_constraints.get("quorum_required", False))
        multi_sig_required = bool(snapshot.governance_constraints.get("multi_sig_required", False))
        if not quorum_required and not multi_sig_required:
            return [ConflictFinding("GOVERNANCE_CONSTRAINT_WEAKENING_CHAIN", "quorum_required", "multi_sig_required", "BLOCKER")]
        return []

    def _rule_dependency_conflicts(self, snapshot: PolicySnapshot) -> List[ConflictFinding]:
        conflicts: List[ConflictFinding] = []
        rules = snapshot.rules
        for rule_name, rule_data in rules.items():
            if not isinstance(rule_data, Mapping):
                continue
            dependencies = rule_data.get("depends_on", [])
            if not isinstance(dependencies, (list, tuple)):
                continue
            for dependency in dependencies:
                dep_name = str(dependency)
                if dep_name not in rules:
                    conflicts.append(ConflictFinding("RULE_DEPENDENCY_CONFLICT", str(rule_name), dep_name, "HIGH"))
        return conflicts
