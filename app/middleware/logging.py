"""Logging middleware for request/response logging."""

import time
import uuid
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger("app.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Log exception
            process_time = (time.time() - start_time) * 1000
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "status_code": 500,
                "process_time_ms": round(process_time, 2),
                "error": str(exc)
            }
            logger.error(json.dumps(log_data))
            raise exc
        else:
            # Log successful request
            process_time = (time.time() - start_time) * 1000
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2)
            }
            logger.info(json.dumps(log_data))
            return response