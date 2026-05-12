import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.control_plane.stability_analyzer import StabilityAnalyzer
from src.services.control_plane.healing_intent_detector import HealingIntentDetector
from src.services.control_plane.noise_detector import NoiseDetector
from src.services.control_plane.healing_budget_controller import HealingBudgetController
from src.services.control_plane.stability_scorer import StabilityScorer
from src.services.control_plane.control_plane_engine import ControlPlaneEngine
from src.services.control_plane.control_plane_orchestrator import ControlPlaneOrchestrator

def test_control_plane():
    orchestrator = ControlPlaneOrchestrator(
        StabilityAnalyzer(),
        HealingIntentDetector(),
        NoiseDetector(),
        HealingBudgetController(),
        StabilityScorer(),
        ControlPlaneEngine()
    )

    telemetry = {
        "accuracy": 0.80,
        "latency": 0.50, # Means 1 - 0.5 = 0.5
        "drift": 0.10,   # Means 1 - 0.1 = 0.9
        "volatility": 0.05
    }
    # Score calculation: 
    # accuracy (0.8 * 0.5 = 0.40) + latency (0.5 * 0.2 = 0.10) + drift (0.9 * 0.3 = 0.27) = 0.77

    history = {
        "recent_heal_count": 4, # triggers OVER_HEALING_RISK
        "last_heal_failed": False
    }

    signals = {
        "metric_variance": 0.2, # stable
        "conflicting_metrics": False
    }

    result = orchestrator.control(telemetry, history, signals)

    assert result["decision"] == "DELAY_HEALING"
    assert result["intent"] == "OVER_HEALING_RISK"
    assert result["noise"] == "STABLE_SIGNAL"
