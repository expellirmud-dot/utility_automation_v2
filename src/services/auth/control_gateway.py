from src.services.audit.audit_logger import AuditLogger


class ControlGateway:
    def __init__(self, rule_engine, audit_logger=None, safety_rules=None):
        self.rule_engine = rule_engine
        if audit_logger is not None and hasattr(audit_logger, "check") and not hasattr(audit_logger, "log"):
            safety_rules = audit_logger
            audit_logger = None
        self.audit = audit_logger or AuditLogger()
        self.safety = safety_rules

    def execute(self, trusted_context, action, system_state, idempotency_key=None):
        role = getattr(trusted_context, "role", trusted_context)
        trusted = getattr(trusted_context, "trusted", True)
        identity_id = getattr(trusted_context, "identity_id", str(role))

        if not trusted:
            self.audit.log(
                event_type="AUTH_FAILURE",
                role="unknown",
                action=action,
                decision="REJECTED_NO_TRUST",
                system_state=system_state,
                idempotency_key=idempotency_key,
            )
            return "REJECTED_NO_TRUST"

        if self.safety is not None and self.safety.check(action, system_state) == "ESCALATE":
            self.audit.log(
                event_type="AUTH_DECISION",
                role=role,
                action=action,
                decision="ESCALATION_REQUIRED",
                system_state=system_state,
                metadata={
                    "identity_id": identity_id,
                    "trust": trusted,
                    "matched_rule": "SafetyEscalation",
                    "rule_id": "SAFETY_ESCALATION",
                    "priority": 1000,
                },
                idempotency_key=idempotency_key,
            )
            return "ESCALATION_REQUIRED"

        if hasattr(self.rule_engine, "evaluate"):
            decision_result = self.rule_engine.evaluate(
                role=role,
                action=action,
                system_state=system_state,
            )
        else:
            decision_result = self.rule_engine.validate(role, action, system_state)
        decision_effect, decision_metadata = _normalize_decision(decision_result)

        if decision_effect == "DENY":
            final_decision = "ACCESS_DENIED"
        elif decision_effect == "ESCALATE":
            final_decision = "ESCALATION_REQUIRED"
        else:
            final_decision = "ACTION_ALLOWED"

        self.audit.log(
            event_type="AUTH_DECISION",
            role=role,
            action=action,
            decision=final_decision,
            system_state=system_state,
            metadata={
                "identity_id": identity_id,
                "trust": trusted,
                **decision_metadata,
            },
            idempotency_key=idempotency_key,
        )

        return final_decision


def _normalize_decision(decision_result):
    if isinstance(decision_result, str):
        return decision_result, {
            "matched_rule": "ActionValidator",
            "rule_id": "ACTION_VALIDATOR",
            "priority": 0,
        }

    return decision_result["decision"], {
        "matched_rule": decision_result["rule_name"],
        "rule_id": decision_result["rule_id"],
        "priority": decision_result["priority"],
    }
