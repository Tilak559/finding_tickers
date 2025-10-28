# Main FastAPI application
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import BaseAPIException
from app.api.router import router as api_router
from app.api.deps import get_request_context, RequestContext
from app.models.responses import HealthCheckResponse

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Application startup time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Max workers: {settings.max_workers}")
    logger.info(f"Rate limit: {settings.rate_limit_per_minute}/min")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A modern API for enriching CSV files with stock ticker symbols",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log requests and responses."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response {request_id}: {response.status_code} (took {duration:.3f}s)"
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response


@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(f"API exception {request_id}: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.__class__.__name__,
            "details": exc.details,
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(f"Validation error {request_id}: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "error_code": "ValidationException",
            "details": exc.errors(),
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(f"HTTP exception {request_id}: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": "HTTPException",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(f"Unexpected error {request_id}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "InternalServerError",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


# Include API routers
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": time.time() - app_start_time,
        "docs_url": "/docs",
        "api_url": "/api/v1"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - app_start_time
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "uptime_seconds": uptime,
        "timestamp": time.time()
    }




if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
