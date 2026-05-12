from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ValidationResult:
    status: str  # "PASS" | "FAIL"
    errors: List[str] = field(default_factory=list)
    severity: str = "LOW" # "LOW" | "HIGH" | "CRITICAL"

@dataclass
class Voucher:
    intent: str
    header: Dict[str, Any]
    budget_context: Dict[str, Any]
    financials: Dict[str, Any]
    workflow: Dict[str, Any]
    compliance: Dict[str, Any]

@dataclass
class FinalVoucherResult:
    voucher: Voucher
    validation: ValidationResult
    intent: str
    confidence: float
    audit_trace: List[str] = field(default_factory=list)
