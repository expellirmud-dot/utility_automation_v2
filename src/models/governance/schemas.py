from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class RuleDefinition:
    rule_id: str
    version: str
    description: str
    logic_params: Dict[str, Any]
    status: str = "ACTIVE" # ACTIVE, DEPRECATED, PENDING
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AuditStep:
    step_id: str
    timestamp: datetime
    step_name: str
    input_data: Dict[str, Any]
    rule_used: str
    rule_version: str
    decision: str
    reason_code: str

@dataclass
class RegressionReport:
    total_cases: int
    changed_cases: int
    risk_score: float
    diff_summary: List[Dict[str, Any]]
    can_deploy: bool
