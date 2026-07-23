"""Health check endpoints"""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "syq",
        "version": settings.VERSION,
        "environment": getattr(settings, 'ENVIRONMENT', 'development')
    }


@router.get("/detailed")
async def detailed_health_check():
    """More detailed health check including dependencies"""
    # In a real implementation, this would check database, redis, etc.
    return {
        "status": "healthy",
        "service": "syq",
        "version": settings.VERSION,
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "checks": {
            "api": "healthy",
            "database": "unknown",  # Would implement actual DB check
            "cache": "unknown"      # Would implement actual cache check
        }
    }