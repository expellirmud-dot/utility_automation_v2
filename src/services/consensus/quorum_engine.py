from typing import Dict, Set
from .causal_models import CausalEvent

class QuorumEngine:
    """
    Transforms a "valid event" into a "globally agreed event".
    Does NOT finalize state. Only collects signatures to reach consensus threshold.
    """
    def __init__(self, node_id: str, validator_registry: Set[str], initial_epoch: int = 1):
        self.node_id = node_id
        self.validator_registry = validator_registry
        self.current_epoch = initial_epoch
        
        # Pending signature collection (event_hash -> Dict[node_id, signature])
        self.signature_pool: Dict[str, Dict[str, str]] = {}

    @property
    def quorum_threshold(self) -> int:
        # N/2 + 1 BFT threshold
        return (len(self.validator_registry) // 2) + 1

    def receive_validated_event(self, event: CausalEvent):
        """Called when Validator Kernel approves the proposal."""
        if event.quorum_state.phase != "VALIDATED":
            raise ValueError(f"Event {event.event_hash} is not VALIDATED.")
            
        event.quorum_state.phase = "QUORUM_PENDING"
        self.signature_pool.setdefault(event.event_hash, {})
        
        # Self-sign the proposal
        self._sign_and_broadcast(event)

    def receive_signature(self, event: CausalEvent, peer_id: str, signature: str) -> bool:
        """
        Receives a signature from a peer.
        Returns True if the event transitions to QUORUM_SATISFIED.
        """
        if peer_id not in self.validator_registry:
            return False # Ignore sybil/unknown signatures
            
        # EPOCH-BOUND QUORUM VALIDITY
        # Signatures are only valid if they belong to the same epoch view.
        if event.epoch != self.current_epoch:
            return False
            
        if event.quorum_state.phase not in ("QUORUM_PENDING", "VALIDATED"):
            return False
            
        # Add to pool
        sigs = self.signature_pool.setdefault(event.event_hash, {})
        sigs[peer_id] = signature
        
        # Check threshold
        if len(sigs) >= self.quorum_threshold:
            event.quorum_state.signatures = sigs
            event.quorum_state.phase = "QUORUM_SATISFIED"
            return True
            
        return False

    def _sign_and_broadcast(self, event: CausalEvent):
        """Stubs the P2P broadcast logic"""
        # In a real system, compute signature here:
        # signature = sign(event.generate_canonical_hash(), self.private_key)
        signature = "dummy_sig_from_" + self.node_id
        self.receive_signature(event, self.node_id, signature)
        # TODO: broadcast to peers
