from src.projections.db_projection_reader import ProjectionReadResult
from src.ui.domain_panels.formatters import (
    format_mesh_panel,
    format_policy_panel,
    format_recovery_panel,
    format_replay_panel,
    format_simulation_panel,
    format_system_health_panel,
)


def _projection(domain: str, *, status: str = "connected") -> ProjectionReadResult:
    return ProjectionReadResult(
        domain=domain,
        status=status,
        source="database_projection" if status != "degraded" else "deterministic_fallback",
        items=(
            {"id": "b", "stable_order": 20, "label": "B"},
            {"id": "a", "stable_order": 10, "label": "A"},
        )
        if status != "degraded"
        else (),
        diagnostics={"reason": "ok", "connected": status != "degraded", "degraded": status == "degraded"},
        metadata={"read_only": True, "projection_only": True, "source_of_truth": "ledger"},
    )


def test_each_domain_formatter_preserves_panel_contract():
    cases = (
        ("recovery", format_recovery_panel),
        ("simulation", format_simulation_panel),
        ("mesh", format_mesh_panel),
        ("policy", format_policy_panel),
        ("replay", format_replay_panel),
        ("system_health", format_system_health_panel),
    )

    for domain, formatter in cases:
        panel = formatter(_projection(domain))
        assert panel["domain"] == domain
        assert panel["advisory_only"] is True
        assert panel["item_count"] == 2
        assert [item["id"] for item in panel["items"]] == ["a", "b"]
        assert [item["id"] for item in panel["summaries"]] == ["a", "b"]
        assert panel["diagnostics"]["connected"] is True
        assert panel["metadata"]["read_only"] is True
        assert panel["metadata"]["projection_only"] is True
        assert panel["metadata"]["source_of_truth"] == "ledger"


def test_degraded_fallback_shape_is_stable():
    panel = format_recovery_panel(_projection("recovery", status="degraded"))

    assert list(panel.keys()) == [
        "domain",
        "status",
        "source",
        "items",
        "advisory_only",
        "item_count",
        "summaries",
        "diagnostics",
        "metadata",
    ]
    assert panel["status"] == "degraded"
    assert panel["source"] == "deterministic_fallback"
    assert panel["items"] == []
    assert panel["item_count"] == 0
    assert panel["summaries"] == []
    assert panel["diagnostics"]["degraded"] is True
