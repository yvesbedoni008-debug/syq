"""Rate limiting middleware to prevent abuse."""

import time
from typing import Dict
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to implement rate limiting."""

    def __init__(self, app, calls: int = None, period: int = None):
        super().__init__(app)
        self.calls = calls or settings.RATE_LIMIT_PER_MINUTE
        self.period = period or 60  # per minute
        self.clients: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        now = time.time()
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]

        # Check if rate limit exceeded
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(self.period)}
            )

        # Add current request
        self.clients[client_ip].append(now)

        # Process request
        response = await call_next(request)
        return response