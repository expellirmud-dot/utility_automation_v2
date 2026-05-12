from src.models.correction_record import CorrectionRecord
from typing import Any

class CorrectionService:
    @staticmethod
    def apply_correction(field_name: str, original: Any, corrected: Any, reason: str, user: str) -> CorrectionRecord:
        return CorrectionRecord(
            field_name=field_name,
            original_value=original,
            corrected_value=corrected,
            correction_reason=reason,
            corrected_by=user
        )
