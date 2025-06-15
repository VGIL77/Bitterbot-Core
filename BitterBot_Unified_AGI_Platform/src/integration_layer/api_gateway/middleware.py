"""
Middleware configuration for BitterBot AGI Platform API Gateway

This module sets up various middleware components for the API.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import logging
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adds a unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs request and response information"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"Request ID: {getattr(request.state, 'request_id', 'unknown')}"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        if client_id in self.clients:
            calls, window_start = self.clients[client_id]
            
            # Reset window if period has passed
            if now - window_start > self.period:
                self.clients[client_id] = (1, now)
            elif calls >= self.calls:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={
                        "Retry-After": str(int(self.period - (now - window_start)))
                    }
                )
            else:
                self.clients[client_id] = (calls + 1, window_start)
        else:
            self.clients[client_id] = (1, now)
            
        response = await call_next(request)
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collects metrics for each request"""
    
    def __init__(self, app, metrics_collector=None):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Record metrics if collector is available
        if self.metrics_collector:
            # TODO: Record request metrics
            pass
            
        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=1000, period=60)
    app.add_middleware(MetricsMiddleware)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception: {exc} "
            f"Request: {request.method} {request.url.path}"
        )
        return Response(
            content="Internal server error",
            status_code=500,
            headers={
                "X-Request-ID": getattr(request.state, "request_id", "unknown")
            }
        )