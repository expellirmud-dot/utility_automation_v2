from src.services.review.review_queue_service import ReviewQueueService

class ReviewWorkflow:
    @staticmethod
    def run(processing_result):
        # Decide if review is needed
        if processing_result.bill_data.confidence_flags or processing_result.ai_review_result:
            return ReviewQueueService.create_item(processing_result)
        return None
