import hashlib
import time
from typing import Callable, Optional
from .causal_models import CausalEvent, QuorumState

class ProposalEngine:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def create_event(self, payload: dict, parents: set, epoch: int) -> CausalEvent:
        # Deterministic generation
        content = f"{self.node_id}:{payload}:{sorted(list(parents))}:{epoch}"
        event_hash = hashlib.sha256(content.encode()).hexdigest()
        return CausalEvent(
            event_hash=event_hash,
            epoch=epoch,
            payload=payload,
            parent_hashes=tuple(sorted(list(parents))),
            quorum_state=QuorumState(phase="PROPOSED", signatures={}, node_id=self.node_id)
        )

class CDMLRuntime:
    """
    The Operational Distributed OS Wrapper.
    Unifies all components into a single Causal Deterministic Mesh Ledger Runtime.
    After finalization, committed events and state snapshots are pushed to Elasticsearch.
    """
    def __init__(self, ledger, validator, quorum, finalizer, projector, sync, proposal,
                 elastic_sink=None):
        self.ledger = ledger
        self.validator = validator
        self.quorum = quorum
        self.finalizer = finalizer
        self.projector = projector
        self.sync = sync
        self.proposal = proposal
        self.elastic_sink = elastic_sink  # Optional: if None, skip indexing
        self.current_epoch = 1

    async def handle_command(self, command: dict):
        """
        Entry point from gov-control.
        Write path: API → CausalEvent → Quorum → Finalizer → DAG → Elasticsearch
        """
        # Create event (Invariant 3: Write is Always Event)
        parents = self.ledger.causal_frontier
        event = self.proposal.create_event(command, parents, self.current_epoch)

        # Phase 1: Validation Gate
        if not self.validator.receive_event(event):
            return {"status": "REJECTED"}

        event.quorum_state.phase = "VALIDATED"

        # Phase 2: Quorum Collection
        self.quorum.receive_validated_event(event)
        # Simulating instantaneous quorum for standalone mode
        event.quorum_state.phase = "QUORUM_SATISFIED"

        # Phase 3: Finalize (Invariant 1: No Direct Mutation)
        committed = self.finalizer.attempt_finalization(event)

        if not committed:
            return {"status": "FAILED_FINALIZATION"}

        # Phase 4: Ledger Append
        self.ledger.admit_validation_phase(event)

        # Phase 5: Publish to Elasticsearch (CQRS Read Model — non-blocking)
        if self.elastic_sink:
            await self.elastic_sink.index_committed_event(event)
            # Also snapshot current state projection
            current_state = self.query_state({}, self._default_apply_fn)
            await self.elastic_sink.snapshot_state(self.current_epoch, current_state)

        return {"status": "OK", "event": event.event_hash}

    def query_state(self, initial_state: dict, apply_fn: Callable):
        """
        Read Path (Invariant 2: Single Truth Source — COMMITTED only)
        """
        return self.projector.project_state(self.current_epoch, initial_state, apply_fn)

    def _default_apply_fn(self, state: dict, event) -> dict:
        new_state = state.copy()
        action = event.payload.get("action")
        if action:
            new_state["actions_executed"] = new_state.get("actions_executed", 0) + 1
            new_state["last_action"] = action
        return new_state

