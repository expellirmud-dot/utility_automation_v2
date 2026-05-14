from typing import Any, Dict, List
from .models import DomainPanelData

class BasePanelFormatter:
    def format(self, data: Any) -> DomainPanelData:
        raise NotImplementedError("Formatters must implement the format method")

class LedgerHealthFormatter(BasePanelFormatter):
    def format(self, data: Dict[str, Any]) -> DomainPanelData:
        # Data expected: { "integrity": bool, "lag": int, "last_seq": int }
        integrity = data.get("integrity", False)
        lag = data.get("lag", 0)
        
        status = "HEALTHY" if integrity and lag < 10 else "DEGRADED" if integrity else "CRITICAL"
        
        return DomainPanelData(
            panel_id="ops.ledger.health",
            title="Ledger Integrity Health",
            domain="ledger",
            summaries=[
                f"Integrity: {'OK' if integrity else 'FAIL'}",
                f"Replication Lag: {lag} events",
            ],
            diagnostics={"integrity_check": integrity, "lag_ms": lag},
            metadata={"last_sequence": data.get("last_seq", 0)},
            item_count=1,
            advisory_only=True,
            health_status=status,
            semantic_score=1.0 if status == "HEALTHY" else 0.5 if status == "DEGRADED" else 0.0
        )

class MeshStabilityFormatter(BasePanelFormatter):
    def format(self, data: Dict[str, Any]) -> DomainPanelData:
        # Data expected: { "active_nodes": int, "divergence_detected": bool, "sync_status": str }
        nodes = data.get("active_nodes", 0)
        divergence = data.get("divergence_detected", False)
        
        status = "STABLE" if not divergence and nodes >= 3 else "UNSTABLE"
        
        return DomainPanelData(
            panel_id="ops.mesh.stability",
            title="Distributed Mesh Stability",
            domain="mesh",
            summaries=[
                f"Active Nodes: {nodes}",
                f"Divergence: {'DETECTED' if divergence else 'NONE'}",
            ],
            diagnostics={"divergence": divergence, "node_count": nodes},
            metadata={"sync_status": data.get("sync_status", "UNKNOWN")},
            item_count=nodes,
            advisory_only=True,
            health_status=status,
            semantic_score=1.0 if status == "STABLE" else 0.3
        )

class PolicyComplianceFormatter(BasePanelFormatter):
    def format(self, data: Dict[str, Any]) -> DomainPanelData:
        # Data expected: { "violations": int, "active_policies": int, "last_audit": str }
        violations = data.get("violations", 0)
        
        status = "COMPLIANT" if violations == 0 else "NON_COMPLIANT"
        
        return DomainPanelData(
            panel_id="ops.policy.compliance",
            title="Policy Compliance Status",
            domain="policy",
            summaries=[
                f"Violations: {violations}",
                f"Active Policies: {data.get('active_policies', 0)}",
            ],
            diagnostics={"violation_count": violations},
            metadata={"last_audit": data.get("last_audit", "N/A")},
            item_count=violations,
            advisory_only=True,
            health_status=status,
            semantic_score=1.0 if status == "COMPLIANT" else 0.2
        )

class RecoveryReadinessFormatter(BasePanelFormatter):
    def format(self, data: Dict[str, Any]) -> DomainPanelData:
        # Data expected: { "snapshot_valid": bool, "backup_age": int, "ready": bool }
        ready = data.get("ready", False)
        
        status = "READY" if ready else "NOT_READY"
        
        return DomainPanelData(
            panel_id="ops.recovery.readiness",
            title="Recovery Readiness Score",
            domain="recovery",
            summaries=[
                f"System Ready: {'YES' if ready else 'NO'}",
                f"Backup Age: {data.get('backup_age', 0)}h",
            ],
            diagnostics={"snapshot_valid": data.get("snapshot_valid", False)},
            metadata={"ready_flag": ready},
            item_count=1,
            advisory_only=True,
            health_status=status,
            semantic_score=1.0 if ready else 0.0
        )


DOMAIN_PANEL_CONFIG = {
    "recovery": ("ops.recovery", "Recovery Projection Panel", 1),
    "simulation": ("ops.simulation", "Simulation Projection Panel", 2),
    "mesh": ("ops.mesh", "Mesh Projection Panel", 1),
    "policy": ("ops.policy", "Policy Projection Panel", 2),
    "replay": ("ops.replay", "Replay Projection Panel", 2),
    "system_health": ("ops.system_health", "System Health Projection Panel", 1),
}


def format_recovery_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("recovery", projection)


def format_simulation_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("simulation", projection)


def format_mesh_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("mesh", projection)


def format_policy_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("policy", projection)


def format_replay_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("replay", projection)


def format_system_health_panel(projection: Dict[str, Any]) -> DomainPanelData:
    return _format_domain_panel("system_health", projection)


def _format_domain_panel(domain: str, projection: Dict[str, Any]) -> DomainPanelData:
    panel_id, title, priority = DOMAIN_PANEL_CONFIG[domain]
    items = _ordered_items(projection.get("items", []))
    degraded = bool(projection.get("degraded", False))
    item_count = len(items)
    health_status = "DEGRADED" if degraded else "EMPTY" if item_count == 0 else "READY"

    diagnostics = {
        "projection_status": projection.get("status", "degraded" if degraded else "connected"),
        "projection_only": True,
        "degraded": degraded,
        **_safe_mapping(projection.get("diagnostics", {})),
    }
    metadata = {
        "bucket": projection.get("bucket", f"ops_{domain}"),
        "ordering": "record_type, sort_order, stable_key",
        "stable_keys": [item["stable_key"] for item in items],
        **_safe_mapping(projection.get("metadata", {})),
    }

    return DomainPanelData(
        panel_id=panel_id,
        title=title,
        domain=domain,
        summaries=_summaries_for(items, degraded),
        diagnostics=diagnostics,
        metadata=metadata,
        item_count=item_count,
        advisory_only=True,
        health_status=health_status,
        semantic_score=_semantic_score(health_status),
        priority=priority,
        recommendations=[],
        evidence_links=[],
    )


def _ordered_items(raw_items: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    items = [item for item in raw_items if isinstance(item, dict)]
    return sorted(
        items,
        key=lambda item: (
            str(item.get("record_type", "")),
            int(item.get("sort_order", 0)),
            str(item.get("stable_key", "")),
        ),
    )


def _summaries_for(items: List[Dict[str, Any]], degraded: bool) -> List[str]:
    if degraded:
        return ["Projection unavailable; degraded read-only fallback active."]
    if not items:
        return ["Projection connected; no records published for this domain."]

    summaries = []
    for item in items:
        payload = item.get("payload", {})
        if not isinstance(payload, dict):
            summaries.append(str(item.get("stable_key", "projection_record")))
            continue
        summary = payload.get("summary") or payload.get("title") or payload.get("detail")
        summaries.append(str(summary or item.get("stable_key", "projection_record")))
    return summaries


def _semantic_score(health_status: str) -> float:
    if health_status == "READY":
        return 1.0
    if health_status == "EMPTY":
        return 0.75
    return 0.0


def _safe_mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}
