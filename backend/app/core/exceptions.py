# Custom exceptions for the application
from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """Base exception for all API-related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class SymbolNotFoundException(BaseAPIException):
    """Raised when a company symbol cannot be found."""
    
    def __init__(self, company_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Symbol not found for company: {company_name}",
            status_code=404,
            details=details or {"company_name": company_name}
        )


class APIRateLimitException(BaseAPIException):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        super().__init__(
            message=message,
            status_code=429,
            details=details or {"retry_after": retry_after}
        )


class FileProcessingException(BaseAPIException):
    """Raised when file processing fails."""
    
    def __init__(self, filename: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File processing failed for {filename}: {reason}",
            status_code=422,
            details=details or {"filename": filename, "reason": reason}
        )


class ValidationException(BaseAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value: Any, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation failed for field '{field}': {reason}",
            status_code=422,
            details=details or {"field": field, "value": str(value), "reason": reason}
        )


class ConfigurationException(BaseAPIException):
    """Raised when configuration is invalid."""
    
    def __init__(self, setting: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Configuration error for '{setting}': {reason}",
            status_code=500,
            details=details or {"setting": setting, "reason": reason}
        )


class ServiceUnavailableException(BaseAPIException):
    """Raised when external service is unavailable."""
    
    def __init__(self, service: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service '{service}' is unavailable: {reason}",
            status_code=503,
            details=details or {"service": service, "reason": reason}
        )
