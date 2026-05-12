from src.services.audit.audit_logger import AuditLogger

class ControlGateway:
    def __init__(self, rule_engine, audit_logger=None):
        self.rule_engine = rule_engine
        self.audit = audit_logger or AuditLogger()

    def execute(self, trusted_context, action, system_state, idempotency_key=None):

        # 🔐 TRUST CHECK (NEW)
        if not trusted_context.trusted:
            self.audit.log(
                event_type="AUTH_FAILURE",
                role="unknown",
                action=action,
                decision="REJECTED_NO_TRUST",
                system_state=system_state,
                idempotency_key=idempotency_key
            )
            return "REJECTED_NO_TRUST"

        # 🧠 DETERMINISTIC RULE ENGINE
        decision_result = self.rule_engine.evaluate(
            role=trusted_context.role,
            action=action,
            system_state=system_state
        )

        decision_effect = decision_result["decision"]
        if decision_effect == "DENY":
            final_decision = "ACCESS_DENIED"
        elif decision_effect == "ESCALATE":
            final_decision = "ESCALATION_REQUIRED"
        else:
            final_decision = "ACTION_ALLOWED"

        # 📜 AUDIT WITH REAL IDENTITY & RULE METADATA
        self.audit.log(
            event_type="AUTH_DECISION",
            role=trusted_context.role,
            action=action,
            decision=final_decision,
            system_state=system_state,
            metadata={
                "identity_id": trusted_context.identity_id,
                "trust": trusted_context.trusted,
                "matched_rule": decision_result["rule_name"],
                "rule_id": decision_result["rule_id"],
                "priority": decision_result["priority"]
            },
            idempotency_key=idempotency_key
        )

        return final_decision
