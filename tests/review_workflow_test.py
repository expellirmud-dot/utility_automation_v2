from src.models.review_item import ReviewItem
from src.models.bill_data import BillData
from src.workflows.review_workflow import ReviewWorkflow

def test_workflow():
    # Mock result
    class MockResult:
        source_file = "test.pdf"
        bill_data = BillData(vendor_name="NT", confidence_flags=["missing_total"])
        ai_review_result = None
        trigger_reason = "Test trigger"
        
    item = ReviewWorkflow.run(MockResult())
    print(f"Review Item Created: {item.source_file}, Status: {item.review_status}")

if __name__ == "__main__":
    test_workflow()
