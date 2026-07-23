"""API router for version 1."""

from fastapi import APIRouter

from app.api.v1.endpoints import opportunities, auth, users, search, trust_signals, ws

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(trust_signals.router, prefix="/trust-signals", tags=["trust-signals"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])