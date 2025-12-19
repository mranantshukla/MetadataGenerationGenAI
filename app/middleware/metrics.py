# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.config.settings import get_settings

settings = get_settings()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests'
)

DOCUMENT_PROCESSING_COUNT = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status', 'file_type']
)

DOCUMENT_PROCESSING_DURATION = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['file_type']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.ENABLE_METRICS:
            return await call_next(request)
        
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        ACTIVE_REQUESTS.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
        finally:
            ACTIVE_REQUESTS.dec()


def setup_metrics(app):
    """Setup metrics middleware."""
    if settings.ENABLE_METRICS:
        app.add_middleware(MetricsMiddleware)
        
        @app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            return Response(
                content=generate_latest(),
                media_type="text/plain"
            )
    
    return app

