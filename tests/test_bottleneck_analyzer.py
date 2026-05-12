import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.performance.bottleneck_analyzer import BottleneckAnalyzer

def test_bottleneck_detection():
    analyzer = BottleneckAnalyzer()

    fake_stats = {
        "SEMANTIC": {"avg": 1.2, "max": 2.0, "min": 0.5, "calls": 100},
        "FINANCIAL": {"avg": 0.2, "max": 0.5, "min": 0.1, "calls": 100},
        "OCR": {"avg": 2.5, "max": 3.0, "min": 2.0, "calls": 100}
    }

    bottlenecks = analyzer.detector.detect(fake_stats)

    assert len(bottlenecks) == 2
    
    # Check if they are identified correctly (OCR is > 2.0 so CRITICAL, SEMANTIC is > 1.0 so HIGH)
    ocr_b = next(b for b in bottlenecks if b["stage"] == "OCR")
    assert ocr_b["severity"] == "CRITICAL"
    
    sem_b = next(b for b in bottlenecks if b["stage"] == "SEMANTIC")
    assert sem_b["severity"] == "HIGH"

def test_root_cause_and_report():
    analyzer = BottleneckAnalyzer()
    
    # Mock telemetry collector's get_stats
    analyzer.telemetry.get_stats = lambda: {
        "SEMANTIC": {"avg": 1.4, "max": 2.0, "min": 0.5, "calls": 100},
        "FINANCIAL": {"avg": 0.2, "max": 0.5, "min": 0.1, "calls": 100},
    }
    
    report = analyzer.analyze()
    
    assert report["summary"]["total_stages"] == 2
    assert report["summary"]["bottleneck_count"] == 1
    assert report["bottlenecks"][0]["stage"] == "SEMANTIC"
    assert "Complex rule evaluation" in report["root_causes"][0]
    assert report["recommendation"] == "SYSTEM ACCEPTABLE BUT CAN BE OPTIMIZED"
