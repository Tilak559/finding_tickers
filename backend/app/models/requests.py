# Request models for API validation
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class CompanyLookupRequest(BaseModel):
    """Request model for single company lookup."""
    
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Company name to lookup",
        example="Apple Inc"
    )
    
    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name format."""
        if not v or not v.strip():
            raise ValueError("Company name cannot be empty")
        
        # Remove extra whitespace and validate characters
        cleaned = re.sub(r'\s+', ' ', v.strip())
        if not re.match(r'^[a-zA-Z0-9\s\.,&\-\(\)]+$', cleaned):
            raise ValueError("Company name contains invalid characters")
        
        return cleaned


class BulkLookupRequest(BaseModel):
    """Request model for bulk company lookup."""
    
    company_names: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of company names to lookup"
    )
    
    @validator('company_names')
    def validate_company_names(cls, v):
        """Validate list of company names."""
        if not v:
            raise ValueError("Company names list cannot be empty")
        
        validated_names = []
        for name in v:
            if not name or not name.strip():
                continue
            
            cleaned = re.sub(r'\s+', ' ', name.strip())
            if re.match(r'^[a-zA-Z0-9\s\.,&\-\(\)]+$', cleaned):
                validated_names.append(cleaned)
        
        if not validated_names:
            raise ValueError("No valid company names provided")
        
        return validated_names


class CSVEnrichmentRequest(BaseModel):
    """Request model for CSV enrichment."""
    
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="CSV filename"
    )
    
    page_size: Optional[int] = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of rows to process per page"
    )
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename format."""
        if not v.endswith('.csv'):
            raise ValueError("File must be a CSV file")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
            raise ValueError("Filename contains invalid characters")
        
        return v


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)"
    )
    
    size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size"
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.size
