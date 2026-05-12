import hashlib
import json
import random
import uuid
from typing import List, Dict, Any
from src.services.mesh.mesh_nodes import LeaderNode, WorkerNode, MeshNode
from src.services.event_sourcing.canonical_event import CanonicalEvent
from src.services.event_sourcing.projection.state_projector import StateProjector

class AdversarialFaultInjector:
    """
    Injects malicious or malformed data into the mesh to test resilience.
    """
    @staticmethod
    def create_forged_event(last_event: CanonicalEvent) -> CanonicalEvent:
        # Forge an event with correct prev_hash but invalid signature/payload
        return CanonicalEvent(
            event_id=str(uuid.uuid4()),
            epoch=last_event.epoch,
            seq_id=last_event.seq_id + 1,
            timestamp="2026-01-01T00:00:00",
            actor="MALICIOUS_ACTOR",
            type="POLICY_UPDATE",
            payload={"rule_id": "FORGED", "logic": "ALLOW_ALL"},
            signature="FAKE_SIG",
            prev_hash=last_event.global_chain_hash,
            global_chain_hash="FAKE_HASH",
            version=1
        )

    @staticmethod
    def create_duplicate_event(event: CanonicalEvent) -> CanonicalEvent:
        # Exact copy of an existing event
        return event

    @staticmethod
    def create_broken_chain_event(last_event: CanonicalEvent) -> CanonicalEvent:
        # Correct everything EXCEPT prev_hash
        return CanonicalEvent(
            event_id=str(uuid.uuid4()),
            epoch=last_event.epoch,
            seq_id=last_event.seq_id + 1,
            timestamp="2026-01-01T00:00:00",
            actor="attacker",
            type="POLICY_UPDATE",
            payload={},
            signature="sig",
            prev_hash="BROKEN_HASH",
            global_chain_hash="SOME_HASH",
            version=1
        )
