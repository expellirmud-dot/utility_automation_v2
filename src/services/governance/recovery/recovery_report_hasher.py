"""
Deterministic Recovery Report Hashing.

Produces canonical, stable hashes for recovery proposals and reports.
AI advice is explicitly excluded from all hashes.
"""

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """
    Convert value to canonical JSON.
    - Sorted keys
    - Sorted lists (converted from tuples)
    - No timestamps
    - No Python object repr
    """
    canonical_value = _canonicalize(value)
    return json.dumps(canonical_value, sort_keys=True, separators=(",", ":"))


def _canonicalize(value: Any) -> Any:
    """Recursively canonicalize a value."""
    if isinstance(value, dict):
        # Sort keys and canonicalize values
        return {str(k): _canonicalize(value[k]) for k in sorted(value.keys())}
    elif isinstance(value, (tuple, list)):
        # Convert to list and sort for determinism
        items = [_canonicalize(v) for v in value]
        # If all items are hashable (strings/numbers), sort them
        try:
            return sorted(items)
        except TypeError:
            # If not sortable, keep order
            return items
    else:
        return value


def stable_hash(value: Any) -> str:
    """Compute SHA256 hash of canonical value."""
    canon_json = canonical_json(value)
    return hashlib.sha256(canon_json.encode()).hexdigest()


def compute_signal_hash(signal) -> str:
    """
    Hash a RecoverySignal (deterministically, excluding metadata timestamps).
    """
    payload = {
        "source": signal.source,
        "signal_type": signal.signal_type,
        "severity": signal.severity,
        "epoch": signal.epoch,
        "seq_id": signal.seq_id,
        "evidence_hashes": sorted(signal.evidence_hashes),
        # metadata is included as-is (must already be frozen/deterministic)
    }
    if signal.metadata:
        payload["metadata"] = dict(signal.metadata)

    return stable_hash(payload)


def compute_diagnosis_hash(diagnosis) -> str:
    """Hash a RecoveryDiagnosis deterministically."""
    payload = {
        "classification": diagnosis.classification,
        "identified_failures": sorted(diagnosis.identified_failures),
        "root_cause_hypothesis": diagnosis.root_cause_hypothesis,
        "confidence": diagnosis.confidence,
        "evidence_count": diagnosis.evidence_count,
    }
    return stable_hash(payload)


def compute_step_hash(step) -> str:
    """Hash a single RecoveryStep deterministically."""
    payload = {
        "step_type": step.step_type,
        "target": step.target,
        "reason": step.reason,
        "parameters": dict(step.parameters) if step.parameters else {},
    }
    return stable_hash(payload)


def compute_plan_hash(plan) -> str:
    """Hash a RecoveryPlan deterministically."""
    # Steps are already sorted by RecoveryPlan.__post_init__
    step_hashes = [compute_step_hash(s) for s in plan.steps]
    
    payload = {
        "step_hashes": step_hashes,
        "estimated_duration_seconds": plan.estimated_duration_seconds,
        "rollback_plan_hash": plan.rollback_plan_hash,
    }
    return stable_hash(payload)


def compute_proposal_hash(proposal) -> str:
    """
    Hash a RecoveryProposal deterministically.
    AI advice is NEVER included in this hash.
    """
    signal_hash = compute_signal_hash(proposal.signal)
    diagnosis_hash = compute_diagnosis_hash(proposal.diagnosis)
    plan_hash = compute_plan_hash(proposal.plan)

    payload = {
        "signal_hash": signal_hash,
        "diagnosis_hash": diagnosis_hash,
        "plan_hash": plan_hash,
        "reason_for_proposal": proposal.reason_for_proposal,
    }
    return stable_hash(payload)


def compute_report_hash(report) -> str:
    """
    Hash a RecoveryReport deterministically.
    AI advice is NEVER included in this hash.
    """
    proposal_hash = report.proposal.proposal_hash
    
    payload = {
        "proposal_hash": proposal_hash,
    }
    return stable_hash(payload)


def verify_signal_hash(signal, expected_hash: str) -> bool:
    """Verify a signal's deterministic hash."""
    return compute_signal_hash(signal) == expected_hash


def verify_diagnosis_hash(diagnosis, expected_hash: str) -> bool:
    """Verify a diagnosis's deterministic hash."""
    return compute_diagnosis_hash(diagnosis) == expected_hash


def verify_plan_hash(plan, expected_hash: str) -> bool:
    """Verify a plan's deterministic hash."""
    return compute_plan_hash(plan) == expected_hash


def verify_proposal_hash(proposal, expected_hash: str) -> bool:
    """Verify a proposal's deterministic hash (excluding AI)."""
    return proposal.proposal_hash == expected_hash


def verify_report_hash(report, expected_hash: str) -> bool:
    """Verify a report's deterministic hash (excluding AI)."""
    return report.report_hash == expected_hash
