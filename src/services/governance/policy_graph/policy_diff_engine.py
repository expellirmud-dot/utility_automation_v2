from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .policy_version import PolicySnapshot, canonical_json, unfreeze_value


@dataclass(frozen=True)
class PolicyDiffChange:
    section: str
    path: str
    operation: str
    before: Any = None
    after: Any = None


@dataclass(frozen=True)
class PolicyDiff:
    from_version_id: str
    to_version_id: str
    changes: Tuple[PolicyDiffChange, ...]


class PolicyDiffEngine:
    SECTIONS = ("rules", "thresholds", "permissions", "governance_constraints")

    def __init__(self, graph_engine):
        self.graph_engine = graph_engine

    def diff(self, from_version_id: str, to_version_id: str) -> PolicyDiff:
        from_version = self.graph_engine.get_version(from_version_id)
        to_version = self.graph_engine.get_version(to_version_id)
        changes = self.diff_snapshots(from_version.snapshot, to_version.snapshot)
        return PolicyDiff(from_version_id, to_version_id, changes)

    def diff_snapshots(self, before: PolicySnapshot, after: PolicySnapshot) -> Tuple[PolicyDiffChange, ...]:
        changes: List[PolicyDiffChange] = []
        before_payload = before.to_payload(include_hash=False)
        after_payload = after.to_payload(include_hash=False)

        for section in self.SECTIONS:
            before_flat = self._flatten(before_payload.get(section, {}))
            after_flat = self._flatten(after_payload.get(section, {}))
            all_paths = sorted(set(before_flat) | set(after_flat))
            for path in all_paths:
                if path not in before_flat:
                    changes.append(PolicyDiffChange(section, path, "added", None, after_flat[path]))
                elif path not in after_flat:
                    changes.append(PolicyDiffChange(section, path, "removed", before_flat[path], None))
                elif canonical_json(before_flat[path]) != canonical_json(after_flat[path]):
                    changes.append(PolicyDiffChange(section, path, "changed", before_flat[path], after_flat[path]))

        return tuple(sorted(changes, key=lambda c: (c.section, c.path, c.operation)))

    def _flatten(self, value: Any, prefix: str = "") -> Dict[str, Any]:
        value = unfreeze_value(value)
        if not isinstance(value, dict):
            return {prefix or "$": value}

        flattened: Dict[str, Any] = {}
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            child = value[key]
            if isinstance(child, dict):
                flattened.update(self._flatten(child, path))
            else:
                flattened[path] = child
        return flattened
