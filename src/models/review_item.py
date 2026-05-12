from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from src.models.bill_data import BillData
from src.models.ai_review_result import AIReviewResult
from src.models.review_status import ReviewStatus

@dataclass
class ReviewItem:
    source_file: str
    provider_name: str
    extracted_bill_data: BillData
    ai_review_result: Optional[AIReviewResult]
    validation_flags: List[str]
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    review_priority: int = 1
    trigger_reason: str = ""
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
