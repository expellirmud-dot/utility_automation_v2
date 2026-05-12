from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple
import hashlib
import json


POLICY_VERSION_CREATED = "POLICY_VERSION_CREATED"
POLICY_VERSION_ROLLBACK = "POLICY_VERSION_ROLLBACK"
POLICY_STAGE_PROMOTED = "POLICY_STAGE_PROMOTED"

POLICY_STAGES = ("draft", "simulation", "approved", "production")


def canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): canonicalize(value[k]) for k in sorted(value)}
    if isinstance(value, tuple):
        return [canonicalize(v) for v in value]
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): freeze_value(value[k]) for k in sorted(value)})
    if isinstance(value, list):
        return tuple(freeze_value(v) for v in value)
    if isinstance(value, tuple):
        return tuple(freeze_value(v) for v in value)
    return value


def unfreeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: unfreeze_value(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [unfreeze_value(v) for v in value]
    return value


@dataclass(frozen=True)
class PolicySnapshot:
    rules: Mapping[str, Any] = field(default_factory=dict)
    thresholds: Mapping[str, Any] = field(default_factory=dict)
    permissions: Mapping[str, Any] = field(default_factory=dict)
    governance_constraints: Mapping[str, Any] = field(default_factory=dict)
    snapshot_hash: str = ""

    def __post_init__(self):
        object.__setattr__(self, "rules", freeze_value(self.rules))
        object.__setattr__(self, "thresholds", freeze_value(self.thresholds))
        object.__setattr__(self, "permissions", freeze_value(self.permissions))
        object.__setattr__(self, "governance_constraints", freeze_value(self.governance_constraints))
        if not self.snapshot_hash:
            object.__setattr__(self, "snapshot_hash", stable_hash(self.to_payload(include_hash=False)))

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = {
            "rules": unfreeze_value(self.rules),
            "thresholds": unfreeze_value(self.thresholds),
            "permissions": unfreeze_value(self.permissions),
            "governance_constraints": unfreeze_value(self.governance_constraints),
        }
        if include_hash:
            payload["snapshot_hash"] = self.snapshot_hash
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PolicySnapshot":
        return cls(
            rules=payload.get("rules", {}),
            thresholds=payload.get("thresholds", {}),
            permissions=payload.get("permissions", {}),
            governance_constraints=payload.get("governance_constraints", {}),
            snapshot_hash=payload.get("snapshot_hash", ""),
        )


@dataclass(frozen=True)
class PolicyVersion:
    version_id: str
    snapshot: PolicySnapshot
    parent_version_ids: Tuple[str, ...]
    stage: str
    actor: str
    reason: str
    ledger_event_id: str
    ledger_global_hash: str
    ledger_seq_id: int
    ledger_timestamp: Any
    rollback_target_id: Optional[str] = None

    def __post_init__(self):
        if self.stage not in POLICY_STAGES:
            raise ValueError(f"Unsupported policy stage: {self.stage}")
        object.__setattr__(self, "parent_version_ids", tuple(sorted(self.parent_version_ids)))

    def with_stage(self, stage: str, event) -> "PolicyVersion":
        return PolicyVersion(
            version_id=self.version_id,
            snapshot=self.snapshot,
            parent_version_ids=self.parent_version_ids,
            stage=stage,
            actor=self.actor,
            reason=self.reason,
            ledger_event_id=event.event_id,
            ledger_global_hash=event.global_chain_hash,
            ledger_seq_id=event.seq_id,
            ledger_timestamp=event.timestamp,
            rollback_target_id=self.rollback_target_id,
        )


@dataclass(frozen=True)
class PolicyPromotionEvent:
    version_id: str
    from_stage: str
    to_stage: str
    quorum_proof: Tuple[str, ...]
    actor: str
    timestamp: Any

    def to_payload(self) -> dict:
        return {
            "version_id": self.version_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "quorum_proof": list(self.quorum_proof),
            "actor": self.actor,
            "timestamp": self.timestamp,
        }
