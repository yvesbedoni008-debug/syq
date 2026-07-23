"""Mission management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import MissionService
from app.schemas import MissionCreate, MissionUpdate, Mission, MissionVersion
from app.core.security import get_current_user
from typing import List
import json

router = APIRouter()


@router.post("/", response_model=Mission)
async def create_mission(
    mission_in: MissionCreate,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new mission"""
    mission_service = MissionService(db)
    return await mission_service.create_mission(current_user.id, mission_in)


@router.get("/", response_model=List[Mission])
async def read_user_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all missions for the current user"""
    mission_service = MissionService(db)
    return await mission_service.get_user_missions(current_user.id, skip=skip, limit=limit)


@router.get("/{mission_id}", response_model=Mission)
async def read_mission(
    mission_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific mission by ID"""
    mission_service = MissionService(db)
    mission = await mission_service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this mission")
    return mission


@router.put("/{mission_id}", response_model=Mission)
async def update_mission(
    mission_id: int,
    mission_in: MissionUpdate,
    current_user: object = Depends(get_current_user),
    db),
    db: AsyncSession = Depends(get_db)
):
    """Update a mission"""
    # Verify mission exists and belongs to user
    mission_service = MissionService(db)
    mission = await mission_service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this mission")

    # Add user ID to the update data for change tracking
    update_data = mission_in.dict(exclude_unset=True)
    if "change_reason" not in update_data:
        update_data["change_reason"] = "Mission updated via API"

    # Update the mission
    updated_mission = await mission_service.update_mission(mission_id, mission_in)
    return updated_mission


@router.get("/{mission_id}/versions", response_model=List[MissionVersion])
async def get_mission_versions(
    mission_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all versions of a mission"""
    # Verify mission exists and belongs to user
    mission_service = MissionService(db)
    mission = await mission_service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this mission")

    versions = await mission_service.get_mission_versions(mission_id)
    return versions


@router.delete("/{mission_id}")
async def delete_mission(
    mission_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a mission"""
    mission_service = MissionService(db)
    mission = await mission_service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this mission")

    # Soft delete by setting is_active to False
    mission_update = MissionUpdate(is_active=False)
    await mission_service.update_mission(mission_id, mission_update)

    return {"message": "Mission deactivated successfully"}