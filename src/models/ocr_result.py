from dataclasses import dataclass

@dataclass
class OCRResult:
    source_type: str  # "text_layer" or "ocr"
    extracted_text: str
    page_count: int
    confidence_notes: str
    processing_time_ms: float
