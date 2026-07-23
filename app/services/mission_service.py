"""Mission service for managing user missions and goals."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.repositories import MissionRepository, OpportunityRepository
from app.schemas import MissionCreate, MissionUpdate
from app.models import Mission, User, mission_version
import logging
import json

logger = logging.getLogger(__name__)


class MissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mission_repo = MissionRepository(db)
        self.opportunity_repo = OpportunityRepository(db)

    async def create_mission(self, user_id: int, mission_in: MissionCreate) -> Mission:
        """Create a new mission for a user."""
        # Verify user exists
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Prepare mission data
        mission_data = mission_in.dict(exclude_unset=True)
        mission_data["user_id"] = user_id

        # Set default values if not provided
        if "priorities" not in mission_data or mission_data["priorities"] is None:
            mission_data["priorities"] = {"trust": 0.2, "value": 0.3, "risk": 0.2, "timeliness": 0.2, "growth": 0.1}
        if "action_boundaries" not in mission_data or mission_data["action_boundaries"] is None:
            mission_data["action_boundaries"] = {
                "may_prepare": ["draft_offer", "gather_docs", "analysis"],
                "requires_approval": ["send_funds", "sign_contract", "legal_commitment"]
            }
        if "approval_rules" not in mission_data or mission_data["approval_rules"] is None:
            mission_data["approval_rules"] = {
                "auto_alert_if": {"trust": 0.8, "score": 0.85},
                "require_approval_for": ["financial_transfer", "legal_signing"]
            }
        if "status" not in mission_data:
            mission_data["status"] = "active"
        if "version_number" not in mission_data:
            mission_data["version_number"] = 1
        if "is_active" not in mission_data:
            mission_data["is_active"] = True
        if "frequency_min_minutes" not in mission_data:
            mission_data["frequency_min_minutes"] = 30
        if "frequency_max_minutes" not in mission_data:
            mission_data["frequency_max_minutes"] = 360
        if "current_frequency_minutes" not in mission_data:
            mission_data["current_frequency_minutes"] = 60

        # Create and save mission
        mission = Mission(**mission_data)
        self.db.add(mission)
        await self.db.commit()
        await self.db.refresh(mission)

        # Create initial version record
        await self._create_version_record(mission, None, "Initial mission creation")

        return mission

    async def get_user_missions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mission]:
        """Get all missions for a specific user."""
        return await self.mission_repo.get_by_user_id(user_id, skip=skip, limit=limit)

    async def get_mission(self, mission_id: int) -> Optional[Mission]:
        """Get a mission by ID."""
        return await self.mission_repo.get(mission_id)

    async def update_mission(
        self,
        mission_id: int,
        mission_in: MissionUpdate
    ) -> Mission:
        """Update an existing mission and create a version record."""
        mission = await self.mission_repo.get(mission_id)
        if not mission:
            raise ValueError("Mission not found")

        # Track what changed for version history
        update_data = mission_in.dict(exclude_unset=True)
        change_reason = update_data.pop("change_reason", "Mission updated via API")
        changed_fields = list(update_data.keys())

        # Update mission fields
        for field, value in update_data.items():
            setattr(mission, field, value)

        # Increment version number
        mission.version_number += 1

        # Save to database
        await self.db.commit()
        await self.db.refresh(mission)

        # Create version record
        await self._create_version_record(mission, changed_fields, change_reason)

        return mission

    async def get_mission_opportunities(self, mission_id: int) -> list:
        """Get opportunities associated with a mission."""
        # First verify the mission exists
        mission = await self.mission_repo.get(mission_id)
        if not mission:
            raise ValueError("Mission not found")

        # Get opportunities linked through mission_opportunities table
        from sqlalchemy import join
        result = await self.db.execute(
            select(self.opportunity_repo.model)
            .select_from(
                join(
                    self.opportunity_repo.model,
                    self.mission_repo.model.__table__.c.id == self.opportunity_repo.model.c.mission_id,
                    isouter=True
                )
            )
            .where(self.mission_repo.model.c.mission_id == mission_id)
        )
        opportunities = result.scalars().all()
        return opportunities

    async def _create_version_record(self, mission: Mission, changed_fields: Optional[List[str]], reason: str):
        """Create a version record for audit/history purposes."""
        version_data = {
            "mission_id": mission.id,
            "version_number": mission.version_number,
            "goal": mission.goal,
            "constraints": mission.constraints,
            "priorities": mission.priorities,
            "action_boundaries": mission.action_boundaries,
            "approval_rules": mission.approval_rules,
            "changed_fields": changed_fields,  # Already a list, JSON column will handle it
            "change_reason": reason,
            "created_by": mission.user_id  # Assuming the user making the change is the owner
        }

        # Insert version record
        stmt = insert(mission_version).values(**version_data)
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_mission_versions(self, mission_id: int) -> list:
        """Get all versions of a mission."""
        from sqlalchemy import select
        from app.models import mission_version

        result = await self.db.execute(
            select(mission_version)
            .where(mission_version.c.mission_id == mission_id)
            .order_by(mission_version.c.version_number.desc())
        )
        versesult = await self.db.execute(
            select(mission_version)
            .where(mission_version.c.mission_id == mission_id)
            .order_by(mission_version.c.version_number.desc())
        )
        versions = result.fetchall()
        return [dict(row) for row in versions]

    async def calculate_adaptive_frequency(self, mission_id: int) -> int:
        """Calculate adaptive frequency based on signal volatility and user engagement."""
        mission = await self.mission_repo.get(mission_id)
        if not mission:
            return 60  # Default to 60 minutes

        # Get recent opportunity activity for this mission
        # This would analyze how frequently new opportunities matching the mission appear
        # For now, return the current frequency
        return mission.current_frequency_minutes