from src.models.review_item import ReviewItem
from src.models.review_status import ReviewStatus

class ReviewQueueService:
    @staticmethod
    def create_item(result) -> ReviewItem:
        return ReviewItem(
            source_file=result.source_file,
            provider_name=result.bill_data.vendor_name or "Unknown",
            extracted_bill_data=result.bill_data,
            ai_review_result=result.ai_review_result,
            validation_flags=result.bill_data.confidence_flags,
            trigger_reason=result.trigger_reason or "Manual Trigger"
        )
