import unittest
import os
import shutil
import uuid
import sys
import sqlite3
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.services.audit.event_ledger import EventLedger
from src.services.audit.audit_logger import AuditLogger
from src.services.auth.control_gateway import ControlGateway
from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
from src.services.rules.default_rules import DEFAULT_RULES
from src.services.identity.context import TrustedContext

from deploy.validation.version_validator import SchemaValidator
from deploy.shared.security.request_signing import RequestSigner

class TestDeploymentRecovery(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"deploy_test_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "events.db")
        
        self.registry = RuleRegistry()
        for r in DEFAULT_RULES:
            self.registry.register(r)
        self.rule_engine = RuleEngine(self.registry)
        
        self.operator_context = TrustedContext({
            "identity_id": "op_99",
            "role": "operator",
            "trusted": True
        })

    def tearDown(self):
        time.sleep(0.1)
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    def test_schema_mismatch_fails_closed(self):
        """Prove that a container starting with an incompatible ledger schema fails closed."""
        # Create a bad schema DB
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE ledger (bad_column TEXT)")
            
        with self.assertRaises(RuntimeError) as context:
            SchemaValidator.validate_ledger_schema(self.db_path)
            
        self.assertIn("Schema mismatch", str(context.exception))

    def test_rolling_restart_determinism(self):
        """Prove that governance yields identical state before and after a simulated container restart."""
        ledger = EventLedger(db_path=self.db_path)
        audit_logger = AuditLogger(ledger_path=self.db_path)
        gateway = ControlGateway(rule_engine=self.rule_engine, audit_logger=audit_logger)
        
        # Pre-restart state
        decision1 = gateway.execute(self.operator_context, "action_a", "NORMAL")
        
        # Simulate deployment / container replacement
        del gateway
        del audit_logger
        del ledger
        
        # Post-restart state
        SchemaValidator.validate_ledger_schema(self.db_path) # Deployment healthcheck
        new_ledger = EventLedger(db_path=self.db_path)
        new_audit = AuditLogger(ledger_path=self.db_path)
        new_gateway = ControlGateway(rule_engine=self.rule_engine, audit_logger=new_audit)
        
        decision2 = new_gateway.execute(self.operator_context, "action_b", "NORMAL")
        
        events = new_ledger.get_all_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["sequence_number"], 1)
        self.assertEqual(events[1]["sequence_number"], 2)

    def test_secret_rotation_isolation(self):
        """Prove that during a partial redeployment with rotated secrets, old containers cannot communicate with new ones."""
        old_signer = RequestSigner("old_secret_1")
        new_signer = RequestSigner("new_secret_2")
        
        # Old container sends request
        sig = old_signer.generate_signature("POST", "/eval", "{}", "100", "nonce1")
        
        # New container verifies
        is_valid = new_signer.verify_signature(sig, "POST", "/eval", "{}", "100", "nonce1")
        
        # Must fail closed
        self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()
