from typing import Dict, List, Set
from .causal_models import CausalEvent

class FinalizerKernel:
    """
    The Ultimate Truth Authority.
    Converts QUORUM_SATISFIED events into COMMITTED irreversible state.
    """
    def __init__(self, ledger_store: Dict[str, CausalEvent]):
        # Direct reference to the CausalClosureLedger's event store
        self.ledger_store = ledger_store
        
        # Atomic locks for causal slots (epoch -> slot_key -> event_hash)
        # Prevents race conditions during check-time vs commit-time
        self.causal_locks: Dict[str, str] = {}

    def attempt_finalization(self, event: CausalEvent) -> bool:
        """
        Attempts to finalize an event using atomic reservation.
        """
        if event.quorum_state.phase != "QUORUM_SATISFIED":
            return False
            
        slot_key = self._get_causal_slot_key(event)
        
        # 1. RESERVE: Atomic causal slot reservation
        if slot_key in self.causal_locks and self.causal_locks[slot_key] != event.event_hash:
            # Another event is holding or has committed this slot
            # Need to trigger conflict resolution (Canonical Ordering)
            if not self._resolve_slot_conflict(event, self.causal_locks[slot_key]):
                event.quorum_state.phase = "REJECTED_FORK"
                return False
                
        # Reserve the slot for ourselves
        self.causal_locks[slot_key] = event.event_hash
            
        # 2. VALIDATE: Transitive commitment check under lock
        if not self._all_parents_committed(event):
            # Rollback reservation if validation fails
            if self.causal_locks.get(slot_key) == event.event_hash:
                del self.causal_locks[slot_key]
            return False

        # 3. COMMIT: Finalize and lock immutably
        event.quorum_state.phase = "FINALIZED"
        self._commit(event)
        return True
        
    def _get_causal_slot_key(self, event: CausalEvent) -> str:
        """A deterministic identifier for the graph topological slot."""
        # Represents: Epoch + Parent combination
        # Any events competing to append to exactly the same parents in the same epoch are in conflict.
        sorted_parents = sorted(list(event.parent_hashes))
        return f"{event.epoch}:{'-'.join(sorted_parents)}"

    def _all_parents_committed(self, event: CausalEvent) -> bool:
        for parent_hash in event.parent_hashes:
            parent_event = self.ledger_store.get(parent_hash)
            if not parent_event or parent_event.quorum_state.phase != "COMMITTED":
                return False
        return True

    def _resolve_slot_conflict(self, incoming_event: CausalEvent, locked_hash: str) -> bool:
        """
        Resolves conflicts using Canonical Ordering.
        Returns True if incoming_event wins and should steal the lock.
        """
        # 1. Epoch (Already gated by Quorum)
        # 2. Causal Depth (Graph Weight)
        # 3. Deterministic Hash
        # Stub logic for demonstration: assume first-come-first-serve wins
        return False

    def _commit(self, event: CausalEvent):
        """Locks the event immutably into the canonical truth DAG."""
        event.quorum_state.phase = "COMMITTED"
        # Triggers downstream State Projection Engine (Phase 3)
