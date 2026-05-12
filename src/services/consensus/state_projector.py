from typing import Dict, Set, Callable
from .causal_models import CausalEvent

class StateProjector:
    """
    Phase 3: The Pure Functional CDML Core.
    Projects state ONLY from COMMITTED DAG events.
    """
    def __init__(self, ledger_store: Dict[str, CausalEvent]):
        # Direct reference to the CausalClosureLedger's event store
        self.ledger_store = ledger_store

    def project_state(self, epoch: int, initial_state: dict, apply_fn: Callable[[dict, CausalEvent], dict]) -> dict:
        """
        state(epoch) = f(committed_subgraph(epoch))
        Strictly consumes ONLY COMMITTED events for the given epoch.
        """
        # Filter: Only committed events, scoped to the requested epoch
        committed_subgraph = [
            event for event in self.ledger_store.values()
            if event.quorum_state.phase == "COMMITTED" and event.epoch == epoch
        ]
        
        # Enforce deterministic reduction traversal (e.g. sorted by canonical hash)
        # Since apply_fn is commutative, order technically doesn't change outcome, 
        # but sorting guarantees execution determinism across runtimes.
        sorted_subgraph = sorted(committed_subgraph, key=lambda e: e.event_hash)
        
        state = initial_state.copy()
        
        for event in sorted_subgraph:
            # apply_fn must be a pure, idempotent, commutative function
            state = apply_fn(state, event)
            
        return state
