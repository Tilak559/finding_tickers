# Core API endpoints - Simplified to 4 essential endpoints
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile
from fastapi.responses import FileResponse
from app.models.requests import CompanyLookupRequest
from app.models.responses import SymbolResponse, EnrichmentResult, HealthCheckResponse
from app.services.enrichment_service import EnrichmentService
from app.services.file_service import FileService
from app.core.logging import get_logger
from app.core.exceptions import BaseAPIException
import os

logger = get_logger(__name__)
router = APIRouter()


def get_enrichment_service() -> EnrichmentService:
    """Dependency to get enrichment service."""
    return EnrichmentService()


def get_file_service() -> FileService:
    """Dependency to get file service."""
    return FileService()


@router.get("/lookup", response_model=SymbolResponse, tags=["single-company"])
async def lookup_single_company(
    company_name: str = Query(..., description="Company name to lookup"),
    service: EnrichmentService = Depends(get_enrichment_service)
):
    """
    2. Single company lookup - Get ticker symbol for one company.
    
    Args:
        company_name: Company name to lookup
        service: Enrichment service dependency
        
    Returns:
        SymbolResponse with lookup result
        
    Raises:
        HTTPException: If validation fails or service error occurs
    """
    try:
        logger.info(f"Single company lookup request: {company_name}")
        
        # Validate request
        request = CompanyLookupRequest(company_name=company_name)
        
        # Perform enrichment
        result = service.enrich_single_company(request.company_name)
        
        logger.info(f"Single company lookup completed: {result.company_name} -> {result.symbol}")
        return result
        
    except BaseAPIException as e:
        logger.warning(f"API exception in single lookup: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in single lookup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload", response_model=EnrichmentResult, tags=["upload-csv"])
async def upload_csv_file(
    file: UploadFile,
    service: EnrichmentService = Depends(get_enrichment_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    3. Upload CSV - Upload and enrich CSV file with ticker symbols.
    
    Args:
        file: CSV file to upload and enrich
        service: Enrichment service dependency
        file_service: File service dependency
        
    Returns:
        EnrichmentResult with processing statistics
        
    Raises:
        HTTPException: If file validation fails or processing error occurs
    """
    try:
        logger.info(f"CSV upload request: {file.filename}")
        
        # Perform enrichment
        result = service.enrich_uploaded_file(file)
        
        logger.info(f"CSV enrichment completed: {result.rows_updated}/{result.rows_processed} successful")
        return result
        
    except BaseAPIException as e:
        logger.warning(f"API exception in CSV upload: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in CSV upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download/{filename}", tags=["download-csv"])
async def download_enriched_csv(
    filename: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    4. Download CSV - Download the enriched CSV file.
    
    Args:
        filename: Name of the enriched CSV file to download
        file_service: File service dependency
        
    Returns:
        FileResponse with the enriched CSV file
        
    Raises:
        HTTPException: If file not found or download error occurs
    """
    try:
        logger.info(f"CSV download request: {filename}")
        
        # Ensure filename has .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Check if file exists
        file_path = os.path.join("data", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(status_code=500, detail="File download failed")