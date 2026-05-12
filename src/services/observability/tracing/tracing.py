import uuid
import contextvars
from typing import Optional

# Context variable to store the correlation ID for the current request/thread
correlation_id_ctx = contextvars.ContextVar("correlation_id", default=None)

class TraceContext:
    @staticmethod
    def set_correlation_id(cid: Optional[str] = None):
        if cid is None:
            cid = f"trace_{uuid.uuid4().hex[:12]}"
        correlation_id_ctx.set(cid)
        return cid

    @staticmethod
    def get_correlation_id() -> str:
        cid = correlation_id_ctx.get()
        if cid is None:
            return TraceContext.set_correlation_id()
        return cid

    @staticmethod
    def get_trace_header():
        return {"X-Correlation-ID": TraceContext.get_correlation_id()}
