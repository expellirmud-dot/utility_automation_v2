from typing import Any, Mapping, Tuple

from src.services.global_consistency.policy_conflict_detector import PolicyConflictDetector
from src.services.governance.policy_graph.policy_version import PolicySnapshot, unfreeze_value
from .simulation_report import ConflictFinding


class PolicyConflictPredictor:
    def __init__(self):
        self.detector = PolicyConflictDetector()

    def detect(self, snapshot: PolicySnapshot) -> Tuple[ConflictFinding, ...]:
        rules = self._rules_as_list(snapshot.rules)
        conflicts = []
        for conflict in self.detector.detect(rules):
            conflicts.append(ConflictFinding(
                conflict_type=str(conflict.get("type", "UNKNOWN_CONFLICT")),
                rule_a=str(conflict.get("rule_a", "")),
                rule_b=str(conflict.get("rule_b", "")),
            ))
        return tuple(sorted(conflicts, key=lambda c: (c.conflict_type, c.rule_a, c.rule_b)))

    def _rules_as_list(self, rules: Any):
        unfrozen = unfreeze_value(rules)
        if isinstance(unfrozen, list):
            return [self._rule_with_id(item, str(index)) for index, item in enumerate(unfrozen)]
        if isinstance(unfrozen, Mapping):
            return [
                self._rule_with_id(unfrozen[key], str(key))
                for key in sorted(unfrozen)
            ]
        return []

    def _rule_with_id(self, rule: Any, fallback_id: str):
        if isinstance(rule, Mapping):
            normalized = dict(rule)
            normalized.setdefault("id", fallback_id)
            return normalized
        return {"id": fallback_id, "value": rule}
