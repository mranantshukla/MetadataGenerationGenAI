# app/api/v1/health.py
from fastapi import APIRouter
from datetime import datetime
from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.API_VERSION
    }


@router.get("/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "supported_formats": settings.ALLOWED_EXTENSIONS,
        "metadata_standard": "Dublin Core",
        "features": [
            "Text extraction with OCR fallback",
            "Named Entity Recognition",
            "Document summarization",
            "Document classification",
            "Keyword extraction",
            "Sentiment analysis",
            "Dublin Core metadata mapping",
            "Database persistence",
            "Background job processing"
        ]
    }

