from .event_models import AuditEvent
from .event_ledger import EventLedger

class AuditLogger:

    def __init__(self, ledger_path="ledger/events.db"):
        # Note: ledger_path now points to a database file
        self.ledger = EventLedger(db_path=ledger_path)

    def log(self,
             event_type,
             role,
             action,
             decision,
             system_state,
             metadata=None,
             idempotency_key=None):

        event = AuditEvent(
            event_type=event_type,
            role=role,
            action=action,
            decision=decision,
            system_state=system_state,
            metadata=metadata
        )

        event_id, seq = self.ledger.append(event, idempotency_key=idempotency_key)
        return event_id
