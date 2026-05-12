import json
import random
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.services.performance.bottleneck_analyzer import BottleneckAnalyzer
from src.services.performance.instrumented_pipeline import InstrumentedPipeline

class MockRealPipeline:
    def ocr(self, data):
        # Simulate heavy OCR processing
        time.sleep(random.uniform(1.5, 3.0)) 
        return {"text": "Extracted OCR data"}
        
    def extract(self, ocr_data):
        time.sleep(random.uniform(0.1, 0.3))
        return {"header": {}, "financials": {"net": 500}}
        
    def semantic(self, extracted_data):
        # Simulate complex rule evaluation
        time.sleep(random.uniform(0.8, 1.5))
        return extracted_data
        
    def financial(self, semantic_data):
        time.sleep(random.uniform(0.05, 0.2))
        return semantic_data
        
    def governance(self, financial_data):
        # Simulate audit logging and versioning overhead
        time.sleep(random.uniform(0.2, 0.6))
        return {"decision": "ALLOW"}

def run_stress_test():
    analyzer = BottleneckAnalyzer()
    telemetry = analyzer.instrument()
    
    # Wrap our mock heavy pipeline
    pipeline = InstrumentedPipeline(MockRealPipeline(), telemetry)
    
    total_docs = 10
    print(f"Starting Stress Test ({total_docs} iterations to simulate real-world latency)...")
    
    start_time = time.time()
    for i in range(total_docs):
        print(f"   Processing document {i+1}/{total_docs}...")
        pipeline.process({"id": f"doc_{i}"})
        
    print(f"\nStress Test Completed in {time.time() - start_time:.2f} seconds.")
    print("Generating Performance Report...\n")
    
    report = analyzer.analyze()
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_stress_test()
