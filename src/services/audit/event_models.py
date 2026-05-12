from datetime import datetime, timezone
import uuid

class EventType:
    ACTION_REQUEST = "action_request"
    AUTH_DECISION = "auth_decision"
    SAFETY_CHECK = "safety_check"
    EXECUTION = "execution"
    OVERRIDE = "override"
    SYSTEM_STATE = "system_state"


class AuditEvent:

    def __init__(self,
                 event_type,
                 role,
                 action,
                 decision,
                 system_state,
                 metadata=None):

        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()

        self.event_type = event_type
        self.role = role
        self.action = action
        self.decision = decision
        self.system_state = system_state

        self.metadata = metadata or {}
