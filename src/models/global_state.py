from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class GlobalState:
    total_budget: float
    used_budget: float
    vouchers: List[Dict] = field(default_factory=list)
    active_rules: List[Dict] = field(default_factory=list)

    def remaining_budget(self):
        return self.total_budget - self.used_budget
