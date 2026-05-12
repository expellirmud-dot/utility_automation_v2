import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.dashboard.system_state import SystemStateAggregator
from src.services.dashboard.decision_timeline import DecisionTimelineEngine
from src.services.dashboard.bottleneck_view import BottleneckView
from src.services.dashboard.healing_tracker import HealingTracker
from src.services.dashboard.health_score import SystemHealthScorer
from src.services.dashboard.dashboard_api import DashboardAPI
from src.services.dashboard.cli_view import CLIDashboard

def test_dashboard_api():
    api = DashboardAPI(
        SystemStateAggregator(),
        DecisionTimelineEngine(),
        BottleneckView(),
        HealingTracker(),
        SystemHealthScorer()
    )

    telemetry = {
        "stability": 0.9,
        "p95_latency": 0.2, # 1-0.2 = 0.8
        "drift": 0.1,       # 1-0.1 = 0.9
        "accuracy": 0.95    # 0.95*0.4 = 0.38 + 0.8*0.3=0.24 + 0.9*0.3=0.27 = 0.89
    }

    events = {
        "all": [
            {"ts": 2, "component": "OCR", "action": "scan", "decision": "pass", "reason": "ok"},
            {"ts": 1, "component": "SEMANTIC", "action": "parse", "decision": "fail", "reason": "missing"}
        ],
        "healing": [
            {"status": "HEALED", "time": "2026-05-12T10:00:00Z"},
            {"status": "FAILED", "time": "2026-05-12T10:05:00Z"}
        ]
    }

    control_state = {
        "optimizations": 3
    }

    bottlenecks = [
        {"stage": "OCR", "severity": "CRITICAL"},
        {"stage": "SEMANTIC", "severity": "HIGH"}
    ]

    report = api.render(telemetry, events, control_state, bottlenecks)

    assert report["system_status"] == "STABLE"
    assert report["health_score"] == pytest.approx(0.89)
    assert report["state"]["active_healings"] == 2
    assert report["timeline"][0]["timestamp"] == 1
    assert len(report["bottlenecks"]["top_critical"]) == 2
    assert report["bottlenecks"]["top_critical"][0]["severity"] == "CRITICAL"
    assert report["healing"]["success_rate"] == 0.5
    
    # CLI render (just checking it does not crash)
    cli = CLIDashboard()
    cli.render(report) 
