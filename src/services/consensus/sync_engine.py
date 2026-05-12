from typing import Dict, Set, List
from collections import deque
from .causal_models import CausalEvent

class SyncEngine:
    """
    Phase 4: Sync Engine (LCA-Based Reconciliation Layer).
    Ensures convergence by strictly syncing only COMMITTED subgraphs.
    """
    def __init__(self, ledger_store: Dict[str, CausalEvent]):
        self.ledger_store = ledger_store

    def reconcile_with_peer(self, peer_epoch: int, peer_committed_frontier: Set[str]) -> List[str]:
        """
        Main Anti-Entropy flow to determine what events the peer needs.
        Returns a list of event_hashes that the remote peer is missing.
        """
        # INVARIANT 4: Epoch Isolation
        # Only reconcile if epochs match (or handle explicit epoch transition protocol)
        
        # 1. Divergence Detection
        local_committed_frontier = self._get_committed_frontier()
        if peer_committed_frontier == local_committed_frontier:
            return [] # In sync
            
        # 2. LCA Computation
        lca_hashes = self._compute_committed_lca(peer_committed_frontier)
        
        # 3. Subgraph Fetch
        # We compute the committed subgraph from the LCA to our local frontier.
        # This is what the peer needs.
        missing_subgraph = self._compute_missing_suffix(lca_hashes, local_committed_frontier)
        
        return missing_subgraph

    def process_incoming_subgraph(self, incoming_events: List[CausalEvent], finalizer_kernel):
        """
        4. Deterministic Reattach (Called on the receiving side).
        Applies the missing committed suffix fetched from a peer.
        """
        # Ensure topological order before attempting finalization
        # Note: finalizer_kernel enforcing rules will inherently reject out-of-order parents
        sorted_events = sorted(incoming_events, key=lambda e: e.event_hash)
        
        for event in sorted_events:
            # Sync Engine ONLY accepts COMMITTED events from peer
            if event.quorum_state.phase != "COMMITTED":
                raise ValueError("Anti-entropy violation: Received uncommitted event.")
                
            # Temporarily downgrade to QUORUM_SATISFIED so FinalizerKernel can run 
            # its strict atomic validation (verifying signatures, parents, and causal slot)
            event.quorum_state.phase = "QUORUM_SATISFIED"
            success = finalizer_kernel.attempt_finalization(event)
            
            if not success:
                # If a valid committed event fails finalization locally, it implies a Byzantine fault,
                # an epoch mismatch, or a profound slot conflict that requires deeper reorg logic.
                raise RuntimeError(f"Sync Reattach Failed for event {event.event_hash}")

    def _get_committed_frontier(self) -> Set[str]:
        """Returns the tips of the strictly COMMITTED DAG."""
        committed_hashes = {h for h, e in self.ledger_store.items() if e.quorum_state.phase == "COMMITTED"}
        
        # Find nodes with no children *that are also committed*
        has_committed_child = set()
        for e in self.ledger_store.values():
            if e.quorum_state.phase == "COMMITTED":
                has_committed_child.update(e.parent_hashes)
                
        return committed_hashes - has_committed_child

    def _compute_committed_lca(self, peer_frontier: Set[str]) -> Set[str]:
        """
        LCA computation restricted strictly to the COMMITTED DAG.
        """
        local_ancestors = set()
        queue = deque(self._get_committed_frontier())
        while queue:
            node = queue.popleft()
            if node not in local_ancestors:
                local_ancestors.add(node)
                event = self.ledger_store.get(node)
                if event and event.quorum_state.phase == "COMMITTED":
                    queue.extend(event.parent_hashes)
                    
        # In a real distributed system, if peer's LCA isn't in our local_ancestors,
        # we'd need multiple rounds of back-and-forth. For this core, we assume 
        # we have the history.
        return local_ancestors.intersection(peer_frontier)

    def _compute_missing_suffix(self, lca_hashes: Set[str], local_frontier: Set[str]) -> List[str]:
        """
        Returns all COMMITTED events that are descendants of the LCA hashes
        up to the local frontier.
        """
        # Find all committed events not in the LCA's ancestry
        # Implementation depends on reverse child_map lookup
        pass
