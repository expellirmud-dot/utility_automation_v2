from src.services.ops_console.formatters import (
    format_mesh_panel,
    format_policy_panel,
    format_recovery_panel,
    format_replay_panel,
    format_simulation_panel,
    format_system_health_panel,
)


FORMATTERS = [
    ("recovery", "ops.recovery", format_recovery_panel),
    ("simulation", "ops.simulation", format_simulation_panel),
    ("mesh", "ops.mesh", format_mesh_panel),
    ("policy", "ops.policy", format_policy_panel),
    ("replay", "ops.replay", format_replay_panel),
    ("system_health", "ops.system_health", format_system_health_panel),
]


def as_dict(panel):
    if hasattr(panel, "model_dump"):
        return panel.model_dump()
    return panel.dict()


def projection_payload(domain: str) -> dict:
    return {
        "domain": domain,
        "bucket": f"ops_{domain}",
        "status": "connected",
        "degraded": False,
        "items": [
            {
                "stable_key": "z-record",
                "record_type": "summary",
                "sort_order": 2,
                "payload": {"summary": "third"},
            },
            {
                "stable_key": "a-record",
                "record_type": "summary",
                "sort_order": 2,
                "payload": {"title": "second"},
            },
            {
                "stable_key": "m-record",
                "record_type": "detail",
                "sort_order": 1,
                "payload": {"detail": "first"},
            },
        ],
        "diagnostics": {"reason": "ok", "status": "connected"},
        "metadata": {"bucket": f"ops_{domain}"},
    }


def degraded_projection(domain: str) -> dict:
    return {
        "domain": domain,
        "bucket": f"ops_{domain}",
        "status": "degraded",
        "degraded": True,
        "items": [],
        "diagnostics": {"reason": "database_missing", "status": "degraded"},
        "metadata": {"bucket": f"ops_{domain}"},
    }


def test_domain_formatters_preserve_stable_contract():
    for domain, panel_id, formatter in FORMATTERS:
        panel = as_dict(formatter(projection_payload(domain)))

        assert panel["panel_id"] == panel_id
        assert panel["domain"] == domain
        assert panel["advisory_only"] is True
        assert panel["item_count"] == 3
        assert panel["summaries"] == ["first", "second", "third"]
        assert panel["diagnostics"]["projection_only"] is True
        assert panel["diagnostics"]["degraded"] is False
        assert panel["metadata"]["stable_keys"] == ["m-record", "a-record", "z-record"]


def test_domain_formatters_preserve_degraded_fallback_shape():
    for domain, panel_id, formatter in FORMATTERS:
        panel = as_dict(formatter(degraded_projection(domain)))

        assert panel["panel_id"] == panel_id
        assert panel["domain"] == domain
        assert panel["advisory_only"] is True
        assert panel["item_count"] == 0
        assert panel["health_status"] == "DEGRADED"
        assert panel["summaries"] == ["Projection unavailable; degraded read-only fallback active."]
        assert panel["diagnostics"]["reason"] == "database_missing"
        assert panel["metadata"]["stable_keys"] == []
        assert panel["recommendations"] == []
        assert panel["evidence_links"] == []
