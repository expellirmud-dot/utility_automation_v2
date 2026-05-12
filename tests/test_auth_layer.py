import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.auth.roles import Role
from src.services.auth.auth_engine import AuthEngine
from src.services.auth.action_validator import ActionValidator
from src.services.auth.safety_rules import SafetyRules
from src.services.auth.control_gateway import ControlGateway
from src.services.auth.integrated_control_plane import SecureControlPlane

class MockControlPlane:
    def rollback(self):
        return {"status": "SUCCESS"}
    def override_decision(self):
        return {"status": "SUCCESS"}

def test_viewer_denied():
    auth = AuthEngine()
    validator = ActionValidator(auth)
    safety = SafetyRules()
    gateway = ControlGateway(validator, safety)
    secure_plane = SecureControlPlane(gateway, MockControlPlane())

    # Viewer tries to override decision -> DENY
    res = secure_plane.request_action(Role.VIEWER, "override_decision", "STABLE")
    assert res == "ACCESS_DENIED"

def test_operator_rollback_allowed_in_critical():
    auth = AuthEngine()
    validator = ActionValidator(auth)
    safety = SafetyRules()
    gateway = ControlGateway(validator, safety)
    secure_plane = SecureControlPlane(gateway, MockControlPlane())

    # Operator tries to rollback in STABLE -> DENY (not in permission matrix for Operator)
    res = secure_plane.request_action(Role.OPERATOR, "rollback", "STABLE")
    assert res == "ACCESS_DENIED"

    # Operator tries to rollback in CRITICAL -> ALLOW (safety override highest priority)
    res2 = secure_plane.request_action(Role.OPERATOR, "rollback", "CRITICAL")
    assert res2 == {"status": "SUCCESS"}

def test_escalation():
    auth = AuthEngine()
    validator = ActionValidator(auth)
    safety = SafetyRules()
    gateway = ControlGateway(validator, safety)
    secure_plane = SecureControlPlane(gateway, MockControlPlane())

    # Admin tries to override decision in CRITICAL state -> ESCALATION_REQUIRED
    res = secure_plane.request_action(Role.ADMIN, "override_decision", "CRITICAL")
    assert res == "ESCALATION_REQUIRED"
