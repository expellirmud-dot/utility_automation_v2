from src.models.review_item import ReviewItem
from src.models.verified_bill_data import VerifiedBillData
from src.models.review_status import ReviewStatus
from typing import List

class VerificationService:
    @staticmethod
    def verify(item: ReviewItem, corrections: List) -> VerifiedBillData:
        # Construct verified fields (base + corrections)
        final_fields = item.extracted_bill_data.__dict__.copy()
        for c in corrections:
            final_fields[c.field_name] = c.corrected_value
            
        return VerifiedBillData(
            original_bill=item.extracted_bill_data,
            corrections=corrections,
            final_verified_fields=final_fields,
            verification_status=ReviewStatus.VERIFIED_WITH_CORRECTIONS if corrections else ReviewStatus.VERIFIED
        )
