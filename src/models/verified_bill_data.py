from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from src.models.bill_data import BillData
from src.models.correction_record import CorrectionRecord
from src.models.review_status import ReviewStatus

@dataclass
class VerifiedBillData:
    original_bill: BillData
    corrections: List[CorrectionRecord]
    final_verified_fields: Dict[str, Any]
    verification_status: ReviewStatus
    verified_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
