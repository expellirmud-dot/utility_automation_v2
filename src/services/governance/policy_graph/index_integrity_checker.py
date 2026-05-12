from dataclasses import dataclass
from collections import Counter
from typing import Iterable
import json

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .policy_graph_engine import PolicyGraphEngine
from .policy_version import canonical_json, stable_hash


@dataclass(frozen=True)
class IndexIntegrityResult:
    ok: bool
    reason: str
    ledger_fingerprint: str
    index_fingerprint: str


class IndexIntegrityChecker:
    def __init__(self, store):
        self.store = store

    def verify(self, ledger_events: Iterable[CanonicalEvent]) -> IndexIntegrityResult:
        ledger_events = list(ledger_events)
        ledger_graph = PolicyGraphEngine.rebuild_from_ledger(ledger_events)
        index_graph = PolicyGraphEngine.rebuild_from_ledger(self.store.load_events())

        ledger_fingerprint = self._graph_fingerprint(ledger_graph)
        index_fingerprint = self._graph_fingerprint(index_graph)

        structural_reason = self._structural_corruption_reason(ledger_graph)
        if structural_reason:
            return IndexIntegrityResult(False, structural_reason, ledger_fingerprint, self._row_fingerprint())

        ledger_event_hashes = {event.global_chain_hash for event in ledger_graph.transition_events}
        index_event_hashes = {event.global_chain_hash for event in self.store.load_events()}
        if not ledger_event_hashes.issubset(index_event_hashes):
            return IndexIntegrityResult(False, "MISSING_LEDGER_EVENT", ledger_fingerprint, index_fingerprint)

        if ledger_fingerprint != index_fingerprint:
            return IndexIntegrityResult(False, "EVENT_REPLAY_MISMATCH", ledger_fingerprint, index_fingerprint)

        row_fingerprint = self._row_fingerprint()
        if row_fingerprint != ledger_fingerprint:
            return IndexIntegrityResult(False, "INDEX_ROW_MISMATCH", ledger_fingerprint, row_fingerprint)

        return IndexIntegrityResult(True, "OK", ledger_fingerprint, index_fingerprint)

    def _structural_corruption_reason(self, ledger_graph: PolicyGraphEngine) -> str | None:
        version_rows = self.store.load_versions()
        edge_rows = self.store.load_parent_edges()
        version_ids = [row["version_id"] for row in version_rows]
        counts = Counter(version_ids)
        if any(count > 1 for count in counts.values()):
            return "DUPLICATE_VERSION_ID"

        expected_ids = set(ledger_graph.versions)
        actual_ids = set(version_ids)
        if expected_ids - actual_ids:
            return "MISSING_VERSION"

        edge_pairs = [
            (edge["parent_version_id"], edge["child_version_id"])
            for edge in edge_rows
        ]
        edge_counts = Counter(edge_pairs)
        if any(count > 1 for count in edge_counts.values()):
            return "DUPLICATE_PARENT_EDGE"

        for edge in edge_rows:
            if edge["parent_version_id"] == edge["child_version_id"]:
                return "SELF_CYCLE_EDGE"
            if edge["child_version_id"] not in actual_ids or edge["parent_version_id"] not in actual_ids:
                return "ORPHAN_PARENT_EDGE"

        ordered_rows = sorted(version_rows, key=lambda r: (r["ledger_seq_id"], r["version_id"], r.get("row_id", 0)))
        timestamps = [
            PolicyGraphEngine()._timestamp_sort_key(row["ledger_timestamp"])
            for row in ordered_rows
        ]
        if timestamps != sorted(timestamps):
            return "TIMESTAMP_ORDER_CORRUPTION"

        expected_hash_by_id = {
            version.version_id: version.snapshot.snapshot_hash
            for version in ledger_graph.versions.values()
        }
        for row in version_rows:
            snapshot_payload = json.loads(row["snapshot_json"])
            recomputed_hash = stable_hash({
                "rules": snapshot_payload.get("rules", {}),
                "thresholds": snapshot_payload.get("thresholds", {}),
                "permissions": snapshot_payload.get("permissions", {}),
                "governance_constraints": snapshot_payload.get("governance_constraints", {}),
            })
            if row["snapshot_hash"] != recomputed_hash:
                return "SNAPSHOT_HASH_RECOMPUTE_MISMATCH"
            if row["version_id"] in expected_hash_by_id and row["snapshot_hash"] != expected_hash_by_id[row["version_id"]]:
                return "SNAPSHOT_HASH_MISMATCH"

        return None

    def _graph_fingerprint(self, graph: PolicyGraphEngine) -> str:
        versions = []
        for version in sorted(graph.versions.values(), key=lambda v: v.version_id):
            versions.append({
                "version_id": version.version_id,
                "snapshot_hash": version.snapshot.snapshot_hash,
                "stage": version.stage,
                "parent_version_ids": list(version.parent_version_ids),
                "rollback_target_id": version.rollback_target_id,
                "ledger_global_hash": version.ledger_global_hash,
            })

        events = [
            event.global_chain_hash
            for event in sorted(graph.transition_events, key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash))
        ]
        return stable_hash({"events": events, "versions": versions})

    def _row_fingerprint(self) -> str:
        version_rows = self.store.load_versions()
        edge_rows = self.store.load_parent_edges()
        event_hashes = [
            event.global_chain_hash
            for event in sorted(self.store.load_events(), key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash))
        ]

        parents_by_child = {}
        for edge in edge_rows:
            parents_by_child.setdefault(edge["child_version_id"], [])
            parents_by_child[edge["child_version_id"]].append(edge["parent_version_id"])

        versions = []
        for row in sorted(version_rows, key=lambda r: r["version_id"]):
            versions.append({
                "version_id": row["version_id"],
                "snapshot_hash": row["snapshot_hash"],
                "stage": row["stage"],
                "parent_version_ids": sorted(parents_by_child.get(row["version_id"], [])),
                "rollback_target_id": row["rollback_target_id"],
                "ledger_global_hash": row["ledger_global_hash"],
            })

        return stable_hash({"events": event_hashes, "versions": versions})
