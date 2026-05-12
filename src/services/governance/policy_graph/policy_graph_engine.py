from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json

from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.mesh.mesh_orchestrator import MeshOrchestrator
from src.services.mesh.sync_manager import SyncManager
from .policy_version import (
    POLICY_STAGE_PROMOTED,
    POLICY_VERSION_CREATED,
    POLICY_VERSION_ROLLBACK,
    PolicySnapshot,
    PolicyVersion,
    canonical_json,
)


class PolicyGraphEngine:
    def __init__(self, mesh_orchestrator: Optional[MeshOrchestrator] = None):
        self.mesh_orchestrator = mesh_orchestrator or MeshOrchestrator()
        self.versions: Dict[str, PolicyVersion] = {}
        self.children: Dict[str, List[str]] = {}
        self.transition_events: List[CanonicalEvent] = []

    def create_version(
        self,
        snapshot: PolicySnapshot,
        parent_version_ids: Iterable[str],
        actor: str,
        reason: str,
    ) -> PolicyVersion:
        payload = {
            "snapshot": snapshot.to_payload(),
            "parent_version_ids": sorted(parent_version_ids),
            "stage": "draft",
            "actor": actor,
            "reason": reason,
        }
        event = self._commit_policy_event(POLICY_VERSION_CREATED, payload, actor)
        return self._apply_event(event)

    def get_version(self, version_id: str) -> PolicyVersion:
        if version_id not in self.versions:
            raise ValueError(f"Policy version not found: {version_id}")
        return self.versions[version_id]

    def children_of(self, version_id: str) -> List[PolicyVersion]:
        return [self.versions[child_id] for child_id in sorted(self.children.get(version_id, []))]

    def lineage_of(self, version_id: str) -> List[PolicyVersion]:
        lineage = []
        current = self.get_version(version_id)
        while True:
            lineage.append(current)
            if not current.parent_version_ids:
                break
            current = self.get_version(current.parent_version_ids[0])
        return list(reversed(lineage))

    def get_production_head(self) -> Optional[PolicyVersion]:
        production_versions = [v for v in self.versions.values() if v.stage == "production"]
        if not production_versions:
            return None
        return sorted(production_versions, key=lambda v: (v.ledger_seq_id, v.version_id))[-1]

    def current_head(self) -> Optional[PolicyVersion]:
        if not self.versions:
            return None
        return sorted(self.versions.values(), key=lambda v: (v.ledger_seq_id, v.version_id))[-1]

    def reconstruct_at(self, timestamp: Any) -> PolicySnapshot:
        cutoff = self._timestamp_sort_key(timestamp)
        rebuilt = self.rebuild_from_ledger(
            event for event in self.transition_events
            if self._timestamp_sort_key(event.timestamp) <= cutoff
        )
        head = rebuilt.current_head()
        if not head:
            return PolicySnapshot()
        return head.snapshot

    @classmethod
    def rebuild_from_ledger(cls, events: Iterable[CanonicalEvent]) -> "PolicyGraphEngine":
        graph = cls()
        for event in sorted(events, key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash)):
            if graph._is_committed_policy_event(event):
                graph._apply_event(event)
        return graph

    def _rollback_version(self, target_version_id: str, actor: str, reason: str) -> PolicyVersion:
        target = self.get_version(target_version_id)
        head = self.current_head()
        parent_ids = [] if head is None else [head.version_id]
        payload = {
            "snapshot": target.snapshot.to_payload(),
            "parent_version_ids": parent_ids,
            "stage": "draft",
            "actor": actor,
            "reason": reason,
            "rollback_target_id": target_version_id,
        }
        event = self._commit_policy_event(POLICY_VERSION_ROLLBACK, payload, actor)
        return self._apply_event(event)

    def _promote_local(self, version_id: str, to_stage: str, actor: str) -> PolicyVersion:
        version = self.get_version(version_id)
        payload = self._promotion_payload(version, to_stage, actor, [])
        event = self._commit_policy_event(POLICY_STAGE_PROMOTED, payload, actor)
        return self._apply_event(event)

    def _promote_with_quorum(
        self,
        version_id: str,
        to_stage: str,
        actor: str,
        quorum_signatures: List[str],
    ) -> PolicyVersion:
        version = self.get_version(version_id)
        payload = self._promotion_payload(version, to_stage, actor, quorum_signatures)
        event = self.mesh_orchestrator.submit_critical_event(
            actor,
            POLICY_STAGE_PROMOTED,
            payload,
            quorum_signatures,
        )
        return self._apply_event(event)

    def _promotion_payload(
        self,
        version: PolicyVersion,
        to_stage: str,
        actor: str,
        quorum_signatures: List[str],
    ) -> dict:
        return {
            "version_id": version.version_id,
            "from_stage": version.stage,
            "to_stage": to_stage,
            "quorum_proof": list(quorum_signatures),
            "actor": actor,
            "timestamp": self._ledger_ready_timestamp(),
        }

    def _commit_policy_event(self, event_type: str, payload: dict, actor: str) -> CanonicalEvent:
        event = self.mesh_orchestrator.leader.propose_event(actor, event_type, payload, "POLICY_GRAPH_LOCAL")
        for worker in self.mesh_orchestrator.workers:
            result = worker.apply_event(event)
            if result in ("RECONCILED", "FORK_DETECTED"):
                SyncManager.perform_anti_entropy_sync(worker, self.mesh_orchestrator.leader)
        return event

    def _apply_event(self, event: CanonicalEvent) -> PolicyVersion:
        if not self._is_committed_policy_event(event):
            raise ValueError("Policy graph only accepts committed policy ledger events")

        if event.type in (POLICY_VERSION_CREATED, POLICY_VERSION_ROLLBACK):
            snapshot = PolicySnapshot.from_payload(event.payload["snapshot"])
            parent_ids = tuple(sorted(event.payload.get("parent_version_ids", [])))
            version_id = self._derive_version_id(snapshot.snapshot_hash, parent_ids, event)
            version = PolicyVersion(
                version_id=version_id,
                snapshot=snapshot,
                parent_version_ids=parent_ids,
                stage=event.payload.get("stage", "draft"),
                actor=event.payload.get("actor", event.actor),
                reason=event.payload.get("reason", ""),
                ledger_event_id=event.event_id,
                ledger_global_hash=event.global_chain_hash,
                ledger_seq_id=event.seq_id,
                ledger_timestamp=event.timestamp,
                rollback_target_id=event.payload.get("rollback_target_id"),
            )
            self._store_version(version)
            self._store_event(event)
            return version

        if event.type == POLICY_STAGE_PROMOTED:
            version_id = event.payload["version_id"]
            version = self.get_version(version_id)
            promoted = version.with_stage(event.payload["to_stage"], event)
            self.versions[version_id] = promoted
            self._store_event(event)
            return promoted

        raise ValueError(f"Unsupported policy event type: {event.type}")

    def _store_version(self, version: PolicyVersion):
        if version.version_id in self.versions:
            raise ValueError(f"Duplicate policy version: {version.version_id}")
        self.versions[version.version_id] = version
        for parent_id in version.parent_version_ids:
            self.children.setdefault(parent_id, [])
            if version.version_id not in self.children[parent_id]:
                self.children[parent_id].append(version.version_id)

    def _store_event(self, event: CanonicalEvent):
        if not any(existing.global_chain_hash == event.global_chain_hash for existing in self.transition_events):
            self.transition_events.append(event)
            self.transition_events.sort(key=lambda e: (e.epoch, e.seq_id, e.global_chain_hash))

    def _is_committed_policy_event(self, event: CanonicalEvent) -> bool:
        return (
            event.type in {POLICY_VERSION_CREATED, POLICY_VERSION_ROLLBACK, POLICY_STAGE_PROMOTED}
            and event.payload.get("committed", True) is True
            and bool(event.global_chain_hash)
            and bool(event.signature)
        )

    def _derive_version_id(
        self,
        snapshot_hash: str,
        parent_version_ids: Iterable[str],
        event: CanonicalEvent,
    ) -> str:
        version_material = {
            "snapshot_hash": snapshot_hash,
            "parent_version_ids": sorted(parent_version_ids),
            "ledger_event": {
                "event_id": event.event_id,
                "global_chain_hash": event.global_chain_hash,
                "seq_id": event.seq_id,
                "timestamp": event.timestamp,
                "type": event.type,
            },
        }
        return hashlib.sha256(canonical_json(version_material).encode()).hexdigest()

    def _timestamp_sort_key(self, timestamp: Any):
        if isinstance(timestamp, (int, float)):
            return float(timestamp)
        if isinstance(timestamp, datetime):
            return timestamp.timestamp()
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return float(timestamp)
        return float(timestamp)

    def _ledger_ready_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
