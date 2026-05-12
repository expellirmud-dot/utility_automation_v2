import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.validation.real_world_validator import RealWorldValidator

def test_reality_validation():
    validator = RealWorldValidator()

    predictions = [
        {"doc": "A", "result": {"decision": "APPROVED"}}
    ]

    ground_truth = {
        "A": {"decision": "APPROVED"}
    }

    report = validator.validate(
        predictions,
        ground_truth,
        sim_metrics={"OCR": {"accuracy": 0.95}},
        real_metrics={"OCR": {"accuracy": 0.87}}
    )

    assert "reality_score" in report
    assert report["accuracy"] == 1.0
    
    # 0.87 - 0.95 = -0.08 -> DEGRADING -> Penalty 10
    # Score = 1.0 * 100 - 10 = 90.0
    assert report["reality_score"] == 90.0
    
    # Grade for score <= 90 but > 75 is B
    assert "B" in report["grade"]
