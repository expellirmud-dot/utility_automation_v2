from src.services.ai.review_gate import ReviewGate
from src.services.ai.ai_review_service import AIReviewService
from src.models.bill_data import BillData

class AIValidationWorkflow:
    @staticmethod
    def run(bill: BillData) -> BillData:
        if ReviewGate.should_trigger(bill):
            service = AIReviewService()
            review = service.run_review(bill)
            # Attach review to bill object without overwriting raw data
            bill.extraction_notes.append(f"AI Review Summary: {review.review_summary}")
        return bill
