from dataclasses import dataclass, field
from typing import Set, Dict, Any, Tuple
import json
import hashlib

@dataclass(frozen=True)
class CausalLink:
    target_hash: str
    link_type: str  # "sequential", "concurrent", "merge"

@dataclass
class QuorumState:
    phase: str  # "pending", "validated", "finalized"
    signatures: Dict[str, str] = field(default_factory=dict) # NodeID -> Signature

@dataclass
class CausalEvent:
    event_hash: str
    epoch: int
    payload: Dict[str, Any]
    causal_links: Tuple[CausalLink, ...]  # Strict ordering for determinism
    quorum_state: QuorumState = field(default_factory=lambda: QuorumState(phase="pending"))

    @property
    def parent_hashes(self) -> Set[str]:
        return {link.target_hash for link in self.causal_links}

    @classmethod
    def generate_canonical_hash(cls, epoch: int, payload: dict, causal_links: Tuple[CausalLink, ...]) -> str:
        """
        Generates a strict canonical hash independent of quorum state.
        This forms the core structural identity of the DAG event.
        """
        # Enforce canonical link sorting by target_hash before hashing
        sorted_links = sorted([{"target": l.target_hash, "type": l.link_type} for l in causal_links], key=lambda x: x["target"])
        
        canonical_dict = {
            "epoch": epoch,
            "payload": payload,
            "links": sorted_links
        }
        dump = json.dumps(canonical_dict, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest()
