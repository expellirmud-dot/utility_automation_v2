import json
from typing import List, Dict, Any, Optional
from src.services.event_sourcing.canonical_event import CanonicalEvent

class ForkDetector:
    @staticmethod
    def detect_fork(current_head: CanonicalEvent, incoming_event: CanonicalEvent) -> bool:
        # A fork is detected if the incoming event's prev_hash does not match the current head
        return incoming_event.prev_hash != current_head.global_chain_hash

class CanonicalChainResolver:
    @staticmethod
    def resolve(local_chain: List[CanonicalEvent], remote_chain: List[CanonicalEvent]) -> List[CanonicalEvent]:
        if not local_chain:
            return remote_chain
        if not remote_chain:
            return local_chain

        # Resolution: Highest Epoch -> Longest Chain -> Lowest Hash
        local_head = local_chain[-1]
        remote_head = remote_chain[-1]
        
        if remote_head.epoch > local_head.epoch:
            return remote_chain
        elif remote_head.epoch == local_head.epoch:
            if len(remote_chain) > len(local_chain):
                return remote_chain
            elif len(remote_chain) == len(local_chain):
                if remote_head.global_chain_hash < local_head.global_chain_hash:
                    return remote_chain
        
        return local_chain

class ReconciliationCoordinator:
    def __init__(self, node):
        self.node = node

    def _chain_is_admissible(self, chain: List[CanonicalEvent]) -> bool:
        if not chain:
            return True

        from src.services.event_sourcing.canonical_event import CanonicalEvent
        from src.services.mesh.crypto_provider import CryptoProvider

        last_epoch = -1
        last_seq = -1
        prev_hash = "GENESIS"

        for event in chain:
            event_dict = dict(event.__dict__)
            signing_payload = {
                k: v for k, v in event_dict.items()
                if k not in ("signature", "global_chain_hash")
            }
            if not CryptoProvider.verify(
                self.node.public_key,
                json.dumps(signing_payload, sort_keys=True),
                event.signature
            ):
                return False
            if CanonicalEvent.compute_hash(event_dict) != event.global_chain_hash:
                return False
            if event.prev_hash != prev_hash:
                return False
            if event.epoch < last_epoch:
                return False
            if event.epoch == last_epoch and event.seq_id <= last_seq:
                return False
            prev_hash = event.global_chain_hash
            last_epoch = event.epoch
            last_seq = event.seq_id

        return True

    def reconcile(self, remote_log: List[CanonicalEvent]):
        # 1. Freeze Worker
        print(f"Node {self.node.node_id} freezing for reconciliation...")
        self.node.frozen = True
        
        # 2. Resolve Canonical Chain
        resolver = CanonicalChainResolver()
        candidate_log = resolver.resolve(self.node.event_log, remote_log)
        canonical_log = candidate_log if self._chain_is_admissible(candidate_log) else self.node.event_log
        
        # 3. Replay and Verify
        from src.services.event_sourcing.projection.state_projector import StateProjector
        projected_state = StateProjector.project(canonical_log)
        state_root_hash = projected_state.get("_state_hash")
        if state_root_hash != StateProjector.project(canonical_log).get("_state_hash"):
            raise Exception("Reconciliation failed state_root_hash verification")

        self.node.event_log = list(canonical_log)
        self.node.current_state = projected_state
        self.node.epoch = self.node.event_log[-1].epoch if self.node.event_log else self.node.epoch
        self.node.frozen = False
        
        head = self.node.event_log[-1].event_id if self.node.event_log else "GENESIS"
        print(f"Node {self.node.node_id} reconciliation complete. New head: {head}")
        return "RECONCILED"
