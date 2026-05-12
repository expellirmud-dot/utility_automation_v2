from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class CorrectionRecord:
    field_name: str
    original_value: Any
    corrected_value: Any
    correction_reason: str
    corrected_by: str
    corrected_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
