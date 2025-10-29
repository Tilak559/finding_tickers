# Response models for API responses
from typing import Optional, List, Generic, TypeVar, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class SymbolResponse(BaseModel):
    """Response model for symbol lookup."""
    
    company_name: str = Field(..., description="Original company name")
    symbol: Optional[str] = Field(None, description="Found ticker symbol")
    description: Optional[str] = Field(None, description="Actual stock name/description")
    success: bool = Field(..., description="Whether lookup was successful")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    source: str = Field(default="finnhub", description="Data source")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Lookup timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EnrichmentResult(BaseModel):
    """Response model for enrichment operations."""
    
    message: str = Field(..., description="Operation result message")
    output_file: Optional[str] = Field(None, description="Output file path")
    rows_processed: int = Field(..., ge=0, description="Number of rows processed")
    rows_updated: int = Field(..., ge=0, description="Number of rows updated")
    rows_failed: int = Field(default=0, ge=0, description="Number of rows that failed")
    processing_time_seconds: float = Field(..., ge=0, description="Processing time in seconds")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileDownloadResponse(BaseModel):
    """Response model for file download."""
    
    filename: str = Field(..., description="File name")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    content_type: str = Field(default="text/csv", description="File content type")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Page size")
    pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency statuses")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
