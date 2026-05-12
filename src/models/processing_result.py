from dataclasses import dataclass, field
from typing import Optional
from src.models.bill_data import BillData
from src.models.ai_review_result import AIReviewResult

@dataclass
class ProcessingResult:
    bill_data: BillData
    validation_flags: List[str] = field(default_factory=list)
    ai_review_result: Optional[AIReviewResult] = None
    processing_status: str = "success"
    pipeline_notes: List[str] = field(default_factory=list)
    trigger_reason: Optional[str] = None
    processing_duration_ms: float = 0.0
    source_file: str = ""
    timestamp: str = ""
