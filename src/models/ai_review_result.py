from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AIReviewResult:
    suspicious_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    manual_review_required: bool = False
    review_summary: str = ""
    confidence_assessment: str = ""
    raw_ai_response: str = ""
    parsing_error: Optional[str] = None
