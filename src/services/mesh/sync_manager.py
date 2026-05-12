import time
from typing import Tuple
from src.services.mesh.mesh_nodes import MeshNode

class SyncManager:
    @staticmethod
    def compute_root_hash(node: MeshNode) -> str:
        return node.current_state.get("_state_hash", "UNKNOWN")

    @staticmethod
    def check_for_drift(node_a: MeshNode, node_b: MeshNode) -> Tuple[bool, str]:
        # Level 1: Structural Root Hash
        node_root = SyncManager.compute_root_hash(node_a)
        leader_root = SyncManager.compute_root_hash(node_b)
        if node_root != leader_root:
            return True, "STRUCTURAL_DIVERGENCE"

        # Level 2: Causal signature/hash comparison.
        for local_event, remote_event in zip(node_a.event_log, node_b.event_log):
            if (
                local_event.global_chain_hash != remote_event.global_chain_hash
                or local_event.signature != remote_event.signature
            ):
                return True, "CAUSAL_SIGNATURE_DIVERGENCE"
        if len(node_a.event_log) != len(node_b.event_log):
            return True, "DELTA_AVAILABLE"
        return False, "IN_SYNC"

    @staticmethod
    def perform_anti_entropy_sync(node: MeshNode, leader: MeshNode):
        # Auto-trigger sync on drift
        drift, reason = SyncManager.check_for_drift(node, leader)
        if drift:
            # Delta sync when the local log is a verified prefix of the leader log.
            local_hashes = [event.global_chain_hash for event in node.event_log]
            leader_hashes = [event.global_chain_hash for event in leader.event_log]
            is_prefix = leader_hashes[:len(local_hashes)] == local_hashes

            # Full replay fallback uses the same reconciliation gate when roots or
            # causal signatures diverge beyond a simple suffix delta.
            node.reconciler.reconcile(leader.event_log)
            mode = "DELTA_SYNC" if is_prefix else "FULL_REPLAY_FALLBACK"
            print(f"Anti-Entropy Sync complete for {node.node_id}. Reason: {reason}. Mode: {mode}")
        else:
            print(f"Node {node.node_id} is in sync.")
