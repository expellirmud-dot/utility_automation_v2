from .rule_model import Rule

# Example Default Rules
DEFAULT_RULES = [
    Rule(
        rule_id="R001",
        name="CriticalRollbackOperator",
        priority=100,

        action="rollback",
        required_role="operator",
        required_state="CRITICAL",

        effect="ALLOW"
    ),

    Rule(
        rule_id="R002",
        name="OperatorRollbackDenied",
        priority=50,

        action="rollback",
        required_role="operator",
        required_state=None,

        effect="DENY"
    ),

    Rule(
        rule_id="R003",
        name="CriticalOverrideEscalation",
        priority=120,

        action="override_decision",
        required_role=None,
        required_state="CRITICAL",

        effect="ESCALATE"
    )
]
