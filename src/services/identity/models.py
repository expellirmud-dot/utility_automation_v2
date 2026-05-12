import uuid
from datetime import datetime, timezone

class ActorIdentity:

    def __init__(self, name, role):

        self.identity_id = str(uuid.uuid4())
        self.name = name
        self.role = role

        self.created_at = datetime.now(timezone.utc).isoformat()
        self.active = True
