import json
import os
from src.workflows.extract_bill_workflow import ExtractBillWorkflow

def test_extraction():
    # Mock OCR output
    mock_ocr = """
    NT bill, 1 เม.ย. 69
    Total: 3,210.00
    """
    
    print("Testing extraction on mock data...")
    bill = ExtractBillWorkflow.run(mock_ocr)
    
    print("\nExtracted Data:")
    print(bill)
    
    # Save output
    output_path = os.path.join("output", "bill_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bill.__dict__, f, indent=4, ensure_ascii=False)
    
    print(f"\nExtracted JSON saved to {output_path}")

if __name__ == "__main__":
    test_extraction()
