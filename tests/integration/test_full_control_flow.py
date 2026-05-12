import pytest
from unittest.mock import MagicMock
from src.services.identity.resolver import IdentityResolver
from src.services.identity.trust_registry import TrustRegistry
from src.services.identity.token_service import TokenService
from src.services.auth.auth_engine import AuthEngine
from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
from src.services.rules.rule_model import Rule
from src.services.governance.governance_controller import GovernanceController
from src.services.audit.event_ledger import EventLedger
from src.services.audit.event_models import AuditEvent
from dataclasses import dataclass

@dataclass
class IdentityModel:
    identity_id: str
    name: str
    role: str

def test_full_control_flow():
    # 1. Setup Dependencies
    trust_registry = TrustRegistry()
    token_service = TokenService()
    token_service.verify_token = MagicMock(return_value=True)
    
    identity_resolver = IdentityResolver(trust_registry, token_service)
    
    # Register a test user
    user_id = "user_001"
    secret = "secret123"
    trust_registry.register(IdentityModel(user_id, "Admin User", "SUPERUSER"))
    
    # Setup Rule Registry
    rule_registry = RuleRegistry()
    rule_registry.register(Rule(rule_id="R1", name="AdminAllow", priority=100, action="ALLOW", required_role="SUPERUSER", required_state=None, effect="ALLOW"))
    
    auth_engine = AuthEngine()
    rule_engine = RuleEngine(rule_registry)
    gov_controller = GovernanceController()
    ledger = EventLedger()
    
    # 2. Input
    action = "EXECUTE_CRITICAL_OPERATION"
    context = {"trust_level": "HIGH", "risk_score": 10}
    token = token_service.issue_token(user_id, secret)
    
    # 3. Full Flow Execution
    identity = identity_resolver.resolve(user_id, token, secret)
    assert identity is not None, "Identity resolution failed"
    
    auth_result = auth_engine.is_allowed(identity["role"], action)
    decision = rule_engine.evaluate(identity["role"], action, context)
    
    # Governance Audit Log
    gov_controller.log_decision(
        trace_id="trace_001",
        step_name="RULE_EVALUATION",
        input_data=context,
        rule_used=decision["rule_id"],
        rule_version="1.0",
        decision=decision["decision"],
        reason_code="RULE_MATCH"
    )
    final_action = decision["decision"]
    
    # Governance -> Audit
    event = AuditEvent(
        event_type="CONTROL_DECISION",
        role=identity["role"],
        action=action,
        decision=final_action,
        system_state=context
    )
    ledger.append(event)
    
    # 4. Assertions
    assert final_action is not None
    # EventLedger.append writes to file, we need a way to verify. 
    # For now, we check that the append call didn't crash.
    print("Full control flow integration: PASSED")

if __name__ == "__main__":
    test_full_control_flow()
