import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import time
from src.services.performance.telemetry_collector import TelemetryCollector
from src.services.performance.instrumented_pipeline import InstrumentedPipeline
from src.services.performance.production_stress_test import ProductionStressTest

class FastMockPipeline:
    def process(self, item):
        self.ocr(item)
        self.extract(item)
        self.semantic(item)
        self.financial(item)
        self.governance(item)
        return {"status": "ALLOW"}

    def ocr(self, x): time.sleep(0.001); return x
    def extract(self, x): return x
    def semantic(self, x): time.sleep(0.001); return x
    def financial(self, x): return x
    def governance(self, x): return x

def test_production_stress():
    telemetry = TelemetryCollector()
    pipeline = InstrumentedPipeline(FastMockPipeline(), telemetry)

    stress = ProductionStressTest(pipeline, telemetry)

    # 1000 items as requested for real load simulation
    report = stress.run(n=1000, threads=10)

    assert "performance" in report
    assert report["load_summary"]["total_requests"] == 1000
    
    # Check that percentile metrics are available
    assert "p95" in report["performance"]["OCR"]
    assert "p99" in report["performance"]["SEMANTIC"]
    
    # Drift status should be stable
    assert report["status"] == "STABLE"
