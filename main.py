"""Main FastAPI application with enhanced security and logging"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.api.v1 import api_router
from app.core.config import settings
from app.middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up SYQ application...")
    import app.models  # noqa: F401 — register models with Base.metadata
    from app.core.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down SYQ application...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SYQ helps users answer: 'Is this opportunity worth my attention?'",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add middleware in order (first added is outermost)
app.add_middleware(LoggingMiddleware)  # Logs all requests
app.add_middleware(SecurityHeadersMiddleware)  # Adds security headers
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to SYQ - Opportunity Intelligence Platform",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


# Health check endpoint (outside API version for accessibility)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple database connectivity check
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": "syq",
            "version": settings.VERSION,
            "timestamp": "2024-01-01T00:00:00Z"  # In real implementation, use datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "syq",
            "error": str(e)
        }, 503


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)