import json
from src.services.testing.sample_loader import SampleLoader
from src.workflows.unified_bill_pipeline import UnifiedBillPipeline

def run_validation_regression():
    samples = SampleLoader.get_all_samples()
    print(f"Processing {len(samples)} bills...")
    
    total_bills = len(samples)
    successes = 0
    warnings = 0
    
    for path in samples:
        try:
            bill = UnifiedBillPipeline.run(path)
            if bill.confidence_flags:
                warnings += 1
            successes += 1
        except Exception:
            pass
            
    print(f"\nTotal Bills: {total_bills}")
    print(f"Validated Successfully: {successes}")
    print(f"Bills with Warnings/Flags: {warnings}")

if __name__ == "__main__":
    run_validation_regression()
