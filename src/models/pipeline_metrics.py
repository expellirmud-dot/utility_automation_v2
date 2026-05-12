from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PipelineMetrics:
    stage_durations: dict = field(default_factory=dict)
    ai_triggered: bool = False
    failure_count: int = 0

@dataclass
class FailureSnapshot:
    source_file: str
    pipeline_stage: str
    error: str
    ocr_text: Optional[str] = None
    bill_data: Optional[dict] = None
    timestamp: str = ""

@dataclass
class HealthReport:
    processed_count: int = 0
    failed_count: int = 0
    total_duration_ms: float = 0.0
