import unittest
import os
import shutil
import concurrent.futures
from datetime import datetime
import uuid
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.services.audit.event_ledger import EventLedger
from src.services.audit.event_models import AuditEvent

class TestLedgerHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_ledger_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "events.db")
        self.ledger = EventLedger(db_path=self.db_path)

    def tearDown(self):
        # Give some time for SQLite to release files
        time.sleep(0.5)
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass # Ignore cleanup errors in tests

    def create_dummy_event(self, action="test_action"):
        return AuditEvent(
            event_type="test_event",
            role="operator",
            action=action,
            decision="ALLOW",
            system_state="NORMAL",
            metadata={"test": True}
        )

    def test_concurrent_append(self):
        """Prove that concurrent writes do not corrupt ledger and maintain order."""
        num_threads = 10
        iterations = 20
        
        def append_worker(worker_id):
            ids = []
            for i in range(iterations):
                event = self.create_dummy_event(f"worker_{worker_id}_action_{i}")
                event_id, seq = self.ledger.append(event)
                ids.append(seq)
            return ids

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(append_worker, i) for i in range(num_threads)]
            all_sequences = []
            for f in futures:
                all_sequences.extend(f.result())

        # Verify all sequences are unique and from 1 to total
        all_sequences.sort()
        total_expected = num_threads * iterations
        self.assertEqual(len(all_sequences), total_expected)
        self.assertEqual(all_sequences, list(range(1, total_expected + 1)))

    def test_idempotency(self):
        """Prove that duplicate requests with same idempotency key result in same record and no duplicates."""
        event = self.create_dummy_event("idempotent_action")
        key = "unique_key_123"
        
        id1, seq1 = self.ledger.append(event, idempotency_key=key)
        id2, seq2 = self.ledger.append(event, idempotency_key=key)
        
        self.assertEqual(id1, id2)
        self.assertEqual(seq1, seq2)
        
        all_events = self.ledger.get_all_events()
        self.assertEqual(len(all_events), 1)

    def test_monotonic_ordering(self):
        """Prove that sequence numbers are monotonic even across multiple ledger instances (same DB)."""
        event1 = self.create_dummy_event("action1")
        _, seq1 = self.ledger.append(event1)
        
        # New instance pointing to same DB
        new_ledger = EventLedger(db_path=self.db_path)
        event2 = self.create_dummy_event("action2")
        _, seq2 = new_ledger.append(event2)
        
        self.assertEqual(seq2, seq1 + 1)

if __name__ == "__main__":
    unittest.main()
