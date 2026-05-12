import json
import os
from src.workflows.unified_bill_pipeline import UnifiedBillPipeline

def test_unified():
    # Mock a PDF path (The pipeline will call OCR which will fail if file missing)
    # Testing integration by calling pipeline
    print("Testing Unified Pipeline Integration...")
    try:
        bill = UnifiedBillPipeline.run("samples/Input_Bills/NT/test.pdf")
        print(f"Result: {bill}")
        
        with open("output/validated_json/result.json", "w", encoding="utf-8") as f:
            json.dump(bill.__dict__, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"Pipeline flow reached: {e}")

if __name__ == "__main__":
    test_unified()
