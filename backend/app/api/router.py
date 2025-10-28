# API router - Simplified to core endpoints only
from fastapi import APIRouter
from app.api import enrich

# Create the main router
router = APIRouter()

# Include only the core enrichment endpoints
router.include_router(
    enrich.router
)
