from dataclasses import dataclass
from typing import Optional, List

@dataclass
class BillData:
    vendor_name: Optional[str] = None
    bill_number: Optional[str] = None
    bill_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    vat: Optional[float] = None
    total: Optional[float] = None
    account_number: Optional[str] = None
    service_period: Optional[str] = None
    raw_text: str = ""
    extraction_notes: List[str] = None
    confidence_flags: List[str] = None

    def __post_init__(self):
        if self.extraction_notes is None: self.extraction_notes = []
        if self.confidence_flags is None: self.confidence_flags = []
