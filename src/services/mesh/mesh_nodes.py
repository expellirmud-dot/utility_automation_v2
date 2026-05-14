import hashlib
import json
import math
import time
from typing import List, Dict, Any, Optional
from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.event_sourcing.projection.state_projector import StateProjector
from src.services.governance.invariants.invariant_engine import InvariantEngine
from src.services.mesh.crypto_provider import CryptoProvider
from src.services.mesh.fork_resolver import ForkDetector, ReconciliationCoordinator

class MeshNode:
    def __init__(self, node_id: str, is_leader: bool = False, public_key=None):
        self.node_id = node_id
        self.is_leader = is_leader
        self.event_log: List[CanonicalEvent] = []
        self.current_state = {}
        self.epoch = 0
        self.public_key = public_key
        self.frozen = False
        self.reconciler = ReconciliationCoordinator(self)

    @staticmethod
    def _event_dict(event: CanonicalEvent) -> Dict[str, Any]:
        return dict(event.__dict__)

    @staticmethod
    def _signing_payload(event: CanonicalEvent) -> str:
        data = {
            k: v for k, v in MeshNode._event_dict(event).items()
            if k not in ("signature", "global_chain_hash")
        }
        return json.dumps(data, sort_keys=True)

    def _has_valid_signature(self, event: CanonicalEvent) -> bool:
        return bool(self.public_key) and CryptoProvider.verify(
            self.public_key,
            self._signing_payload(event),
            event.signature
        )

    def _has_valid_global_hash(self, event: CanonicalEvent) -> bool:
        return CanonicalEvent.compute_hash(self._event_dict(event)) == event.global_chain_hash

    def verify_event(self, event: CanonicalEvent) -> bool:
        """
        Strict Worker Verification Gate
        """
        # 1. Signature Verification
        if not self._has_valid_signature(event):
            return False

        # 2. Global Chain Hash Verification
        if not self._has_valid_global_hash(event):
            return False
        
        # 3. Prev Hash Verification
        if self.event_log:
            if event.prev_hash != self.event_log[-1].global_chain_hash:
                return False
        elif event.prev_hash != "GENESIS":
            return False
        
        # 4. Monotonicity (Epoch/Seq)
        if self.event_log:
            if event.epoch < self.epoch: return False
            if event.epoch == self.epoch and event.seq_id <= self.event_log[-1].seq_id:
                return False
        
        return True

    def apply_event(self, event: CanonicalEvent):
        if self.frozen:
            return "FROZEN"

        # PRE-COMMIT GATE
        if not self.verify_event(event):
            # Trigger Fork Resolution if prev_hash is wrong
            if (
                self.event_log
                and ForkDetector.detect_fork(self.event_log[-1], event)
                and self._has_valid_signature(event)
                and self._has_valid_global_hash(event)
            ):
                return self.reconciler.reconcile([*self.event_log, event])
            raise Exception(f"Event verification failed for {event.event_id}")

        # Invariant Check
        if not InvariantEngine.validate_transition(self.current_state, event, {}):
            raise Exception(f"Invariant Violation: Event {event.event_id} rejected")

        self.event_log.append(event)
        self.current_state = StateProjector.project(self.event_log)
        return "SUCCESS"

class LeaderNode(MeshNode):
    def __init__(self, node_id: str, private_key=None, public_key=None):
        if private_key is None:
            private_key, public_key = CryptoProvider.generate_keypair()
        elif public_key is None and hasattr(private_key, "public_key"):
            public_key = private_key.public_key()
        super().__init__(node_id, is_leader=True, public_key=public_key)
        self.private_key = private_key
        self.public_key = public_key

    def propose_event(self, actor: str, event_type: str, payload: Dict[str, Any], quorum_sig: str):
        seq_id = len(self.event_log)
        prev_hash = self.event_log[-1].global_chain_hash if self.event_log else "GENESIS"
        timestamp = self._next_ledger_timestamp()
        
        event_dict = {
            "event_id": str(hashlib.sha256(f"{seq_id}{timestamp}".encode()).hexdigest()),
            "epoch": self.epoch,
            "seq_id": seq_id,
            "timestamp": timestamp,
            "actor": actor,
            "type": event_type,
            "payload": payload,
            "signature": "",
            "prev_hash": prev_hash,
            "version": 1,
            "parent_event_ids": [],
            "causal_depth": seq_id
        }

        event_dict["signature"] = CryptoProvider.sign(
            self.private_key,
            json.dumps(
                {k: v for k, v in event_dict.items() if k not in ("signature", "global_chain_hash")},
                sort_keys=True
            )
        )
        global_hash = CanonicalEvent.compute_hash(event_dict)
        event_dict["global_chain_hash"] = global_hash
        
        event = CanonicalEvent(**event_dict)

        # Pre-commit Invariant Gate
        if not InvariantEngine.validate_transition(self.current_state, event, {}):
            raise Exception("Pre-commit Invariant Violation")

        self.apply_event(event)
        return event

    def _next_ledger_timestamp(self) -> float:
        timestamp = time.time()
        if not self.event_log:
            return timestamp

        previous = float(self.event_log[-1].timestamp)
        if timestamp > previous:
            return timestamp
        return math.nextafter(previous, math.inf)

class WorkerNode(MeshNode):
    def sync_from_leader(self, event_log: List[CanonicalEvent]):
        # Use the Reconciliation Coordinator for a safe sync
        self.reconciler.reconcile(event_log)
