from fastapi import Request
from src.services.observability.tracing.tracing import TraceContext
import time

async def observability_middleware(request: Request, call_next):
    # 1. Trace propagation: Extract or generate correlation ID
    cid = request.headers.get("X-Correlation-ID")
    TraceContext.set_correlation_id(cid)
    
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    # Log duration with correlation ID
    print(f"Trace[{TraceContext.get_correlation_id()}] Request {request.url.path} took {duration:.2f}ms")
    
    response.headers["X-Correlation-ID"] = TraceContext.get_correlation_id()
    return response
