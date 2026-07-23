"""User management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import UserService
from app.schemas import UserCreate, User, UserUpdate, UserProfileCreate, UserProfileUpdate
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me", response_model=dict)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    user_service = UserService(db)
    return await user_service.get_user_profile(current_user.id)


@router.put("/me", response_model=dict)
async def update_user_me(
    user_in: UserUpdate,
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    user_service = UserService(db)
    return await user_service.update_user_profile(
        current_user.id, user_in, profile_in
    )


@router.get("/{user_id}", response_model=dict)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (users can only view their own profile)"""
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    user_service = UserService(db)
    return await user_service.get_user_profile(user_id)