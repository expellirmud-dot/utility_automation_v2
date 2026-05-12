import unittest
import os
import shutil
import uuid
import sys
import threading
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.services.audit.event_ledger import EventLedger
from src.services.audit.audit_logger import AuditLogger
from src.services.audit.replay_engine import ReplayEngine
from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
from src.services.rules.default_rules import DEFAULT_RULES
from src.services.auth.control_gateway import ControlGateway
from src.services.identity.context import TrustedContext

from src.services.testing.chaos.fault_injector import FaultInjector

class TestChaosResilience(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"chaos_data_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "events.db")
        
        # Initialize Core Components
        self.ledger = EventLedger(db_path=self.db_path)
        self.audit_logger = AuditLogger(ledger_path=self.db_path)
        
        self.registry = RuleRegistry()
        for r in DEFAULT_RULES:
            self.registry.register(r)
        self.rule_engine = RuleEngine(self.registry)
        
        self.gateway = ControlGateway(rule_engine=self.rule_engine, audit_logger=self.audit_logger)
        self.fault_injector = FaultInjector()
        
        self.operator_context = TrustedContext({
            "identity_id": "operator_123",
            "role": "operator",
            "trusted": True
        })
        
        self.admin_context = TrustedContext({
            "identity_id": "admin_456",
            "role": "admin",
            "trusted": True
        })

    def tearDown(self):
        self.fault_injector.cleanup()
        time.sleep(0.1)
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    def test_audit_failure_blocks_execution(self):
        """Prove that if audit append fails, the system fails closed (execution blocked)."""
        # Inject failure into ledger append
        original_append = self.audit_logger.ledger.append
        
        def failing_append(*args, **kwargs):
            raise Exception("Simulated DB Crash")
            
        self.audit_logger.ledger.append = failing_append
        
        with self.assertRaises(Exception) as context:
            self.gateway.execute(self.operator_context, "rollback", "CRITICAL")
            
        self.assertIn("Simulated DB Crash", str(context.exception))
        
        # Restore and verify ledger is empty
        self.audit_logger.ledger.append = original_append
        self.assertEqual(len(self.audit_logger.ledger.get_all_events()), 0)

    def test_duplicate_request_suppression(self):
        """Prove that retry storms with the same idempotency key don't corrupt the ledger."""
        key = "idemp_retry_111"
        
        # First request
        decision1 = self.gateway.execute(self.operator_context, "rollback", "CRITICAL", idempotency_key=key)
        
        # Simulated Retry Storm
        for _ in range(5):
            decision_n = self.gateway.execute(self.operator_context, "rollback", "CRITICAL", idempotency_key=key)
            self.assertEqual(decision1, decision_n)
            
        # Verify ledger has exactly 1 event
        events = self.ledger.get_all_events()
        self.assertEqual(len(events), 1)

    def test_identity_untrusted_fails_closed(self):
        """Prove that untrusted identity completely blocks governance and records AUTH_FAILURE."""
        untrusted = TrustedContext({
            "identity_id": "hacker_999",
            "role": "admin",
            "trusted": False
        })
        
        decision = self.gateway.execute(untrusted, "rollback", "CRITICAL")
        self.assertEqual(decision, "REJECTED_NO_TRUST")
        
        events = self.ledger.get_all_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "AUTH_FAILURE")

    def test_wal_crash_recovery_preserves_ordering(self):
        """Prove that after a simulated crash, sequence numbers remain valid and replay is deterministic."""
        # Write some events
        self.gateway.execute(self.operator_context, "action_1", "NORMAL")
        self.gateway.execute(self.admin_context, "action_2", "NORMAL")
        
        # Simulate Crash by throwing away instances and reconnecting
        del self.gateway
        del self.audit_logger
        del self.ledger
        
        # Re-initialize
        new_ledger = EventLedger(db_path=self.db_path)
        events = new_ledger.get_all_events()
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["sequence_number"], 1)
        self.assertEqual(events[1]["sequence_number"], 2)
        
        # Replay validation
        self.assertEqual(events[0]["action"], "action_1")
        self.assertEqual(events[1]["action"], "action_2")

if __name__ == "__main__":
    unittest.main()
