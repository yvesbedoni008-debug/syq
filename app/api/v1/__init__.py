"""API version 1 router"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, opportunities, search, missions, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(health.router, prefix="/health", tags=["health"])