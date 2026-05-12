from typing import Set, List, Dict
from collections import deque
from .causal_models import CausalEvent

class CausalClosureLedger:
    def __init__(self):
        # The ultimate state source: un-ordered mathematical set of validated event hashes
        self.closure_set: Set[str] = set()
        
        # In-memory storage of the actual events (hash -> Event)
        self.event_store: Dict[str, CausalEvent] = {}
        
        # Reverse edge tracking: Parent Hash -> Set of Child Hashes
        self.child_map: Dict[str, Set[str]] = {}

    @property
    def causal_frontier(self) -> Set[str]:
        """Nodes with no known children in the closure set."""
        return {node for node in self.closure_set if not self.child_map.get(node)}

    def validate_causal_closure(self, event: CausalEvent) -> bool:
        """
        Enforce true transitive causal closure.
        If an event is admitted, all its ancestors must already be in the closure set.
        """
        return all(parent in self.closure_set for parent in event.parent_hashes)

    def admit_validation_phase(self, event: CausalEvent) -> bool:
        """
        Phase 1: Validation Quorum.
        Adds the event to the DAG structure after validating causal closure.
        """
        if event.event_hash in self.closure_set:
            return False # Idempotent admission
            
        if not self.validate_causal_closure(event):
            raise ValueError(f"Causal closure violation: Missing ancestors for {event.event_hash}")
                
        # Update Event Store
        self.event_store[event.event_hash] = event
        self.closure_set.add(event.event_hash)
        self.child_map.setdefault(event.event_hash, set())
        
        # Update Reverse Edges
        for parent_hash in event.parent_hashes:
            self.child_map.setdefault(parent_hash, set()).add(event.event_hash)
        
        return True

    def compute_lca(self, remote_frontier: Set[str]) -> Set[str]:
        """
        Computes the Lowest Common Ancestor (LCA) between local frontier and a remote frontier.
        Returns the set of maximal common ancestors under partial order.
        """
        local_ancestors = set()
        remote_ancestors = set()

        # BFS/DFS to build full ancestry set for local
        queue = deque(self.causal_frontier)
        while queue:
            node = queue.popleft()
            if node not in local_ancestors:
                local_ancestors.add(node)
                if node in self.event_store:
                    queue.extend(self.event_store[node].parent_hashes)

        # BFS/DFS to build full ancestry set for remote
        # Note: In a real system, we might need to ask the remote for its parents if we don't have them.
        # Assuming we have the remote frontier nodes or can fetch them.
        queue = deque(remote_frontier)
        while queue:
            node = queue.popleft()
            if node not in remote_ancestors:
                remote_ancestors.add(node)
                if node in self.event_store:
                    queue.extend(self.event_store[node].parent_hashes)

        # Intersection
        common_ancestors = local_ancestors.intersection(remote_ancestors)
        
        # Maximize: keep only nodes that have NO children within the common_ancestors set
        lca = set()
        for node in common_ancestors:
            children_in_common = self.child_map.get(node, set()).intersection(common_ancestors)
            if not children_in_common:
                lca.add(node)
                
        return lca

    def reduce_state(self, initial_state: dict, apply_fn) -> dict:
        """
        State = reduce(apply, causal_closure_set)
        Note: The apply_fn MUST be commutative within an epoch and completely order-invariant.
        Iteration order is deterministic.
        """
        state = initial_state
        # Sorted to guarantee deterministic iteration
        for event_hash in sorted(list(self.closure_set)):
            event = self.event_store[event_hash]
            state = apply_fn(state, event)
        return state

