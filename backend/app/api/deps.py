# API dependencies
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from app.core.logging import get_logger
from app.core.config import settings
import uuid
import time

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_request_id(request: Request) -> str:
    """Generate or retrieve request ID."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


def log_request(request: Request, request_id: str):
    """Log incoming request."""
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )


def log_response(request_id: str, status_code: int, duration: float):
    """Log response."""
    logger.info(
        f"Response {request_id}: {status_code} (took {duration:.3f}s)"
    )


class RequestContext:
    """Request context for dependency injection."""
    
    def __init__(self, request_id: str, start_time: float):
        self.request_id = request_id
        self.start_time = start_time
    
    @property
    def duration(self) -> float:
        """Get request duration."""
        return time.time() - self.start_time


def get_request_context(
    request: Request,
    request_id: str = Depends(get_request_id)
) -> RequestContext:
    """Get request context."""
    start_time = time.time()
    log_request(request, request_id)
    return RequestContext(request_id, start_time)


def validate_api_key(api_key: str = Depends(security)) -> bool:
    """
    Validate API key (placeholder for future authentication).
    
    Args:
        api_key: API key from request
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    # For now, we don't require authentication
    # This is a placeholder for future implementation
    return True


def get_rate_limit_status() -> dict:
    """Get current rate limit status."""
    # This would integrate with the rate limiter
    # For now, return a placeholder
    return {
        "status": "active",
        "requests_per_minute": settings.rate_limit_per_minute,
        "remaining": settings.rate_limit_per_minute
    }
