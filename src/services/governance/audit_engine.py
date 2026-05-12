from typing import List, Dict
from src.models.governance.schemas import AuditStep
import uuid
from datetime import datetime

class AuditDecisionEngine:
    def __init__(self):
        # Traces stored by trace_id -> List of AuditStep
        self.traces: Dict[str, List[AuditStep]] = {}

    def start_trace(self) -> str:
        trace_id = str(uuid.uuid4())
        self.traces[trace_id] = []
        return trace_id

    def log_step(self, trace_id: str, step_name: str, input_data: dict, rule_used: str, rule_version: str, decision: str, reason_code: str) -> AuditStep:
        step = AuditStep(
            step_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            step_name=step_name,
            input_data=input_data,
            rule_used=rule_used,
            rule_version=rule_version,
            decision=decision,
            reason_code=reason_code
        )
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].append(step)
        return step

    def reconstruct_flow(self, trace_id: str) -> List[AuditStep]:
        if trace_id not in self.traces:
            raise ValueError(f"Trace {trace_id} not found")
        # Ensure ordered by timestamp
        return sorted(self.traces[trace_id], key=lambda x: x.timestamp)
