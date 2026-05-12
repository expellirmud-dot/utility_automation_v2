import httpx
import os
import json
from deploy.shared.security.request_signing import RequestSigner

class RemoteRuleEngine:
    def __init__(self, url, secret):
        self.url = url
        self.signer = RequestSigner(secret)

    def evaluate(self, role, action, system_state):
        payload_dict = {"role": role, "action": action, "system_state": system_state}
        payload_str = json.dumps(payload_dict)
        headers = self.signer.sign_request_headers("POST", "/evaluate", payload_str)
        
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{self.url}/evaluate",
                json=payload_dict,
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()

class RemoteAuditLogger:
    def __init__(self, url, secret):
        self.url = url
        self.signer = RequestSigner(secret)

    def log(self, event_type, role, action, decision, system_state, metadata=None, idempotency_key=None):
        payload_dict = {
            "event_type": event_type,
            "role": role,
            "action": action,
            "decision": decision,
            "system_state": system_state,
            "metadata": metadata,
            "idempotency_key": idempotency_key
        }
        payload_str = json.dumps(payload_dict)
        headers = self.signer.sign_request_headers("POST", "/log", payload_str)
        
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{self.url}/log",
                json=payload_dict,
                headers=headers
            )
            resp.raise_for_status()
            return resp.json().get("event_id")

