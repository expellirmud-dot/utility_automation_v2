import os
import json
from src.workflows.process_bill_workflow import ProcessBillWorkflow

def test_workflow():
    sample = "samples/Input_Bills/NT/test.pdf" # Assumed existence
    if not os.path.exists(sample):
        print("Sample missing.")
        return
        
    bill = ProcessBillWorkflow.run(sample)
    print(bill)
    
    with open("output/extracted_json/result.json", "w", encoding="utf-8") as f:
        json.dump(bill.__dict__, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    test_workflow()
