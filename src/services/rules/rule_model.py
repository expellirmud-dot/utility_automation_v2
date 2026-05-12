from dataclasses import dataclass

@dataclass(frozen=True)
class Rule:

    rule_id: str
    name: str

    priority: int

    action: str
    required_role: str | None
    required_state: str | None

    effect: str
