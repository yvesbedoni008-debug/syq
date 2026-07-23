"""Feedback service layer"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import FeedbackRepository
from app.schemas import FeedbackCreate, FeedbackUpdate, Feedback


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feedback_repo = FeedbackRepository(db)

    async def create(self, obj_in: FeedbackCreate) -> Feedback:
        """Create new feedback"""
        db_obj = await self.feedback_repo.create(obj_in)
        return Feedback.from_orm(db_obj)

    async def get(self, id: int) -> Optional[Feedback]:
        """Get feedback by ID"""
        db_obj = await self.feedback_repo.get(id)
        return Feedback.from_orm(db_obj) if db_obj else None

    async def get_by_user_id(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Feedback]:
        """Get feedback by user ID"""
        db_objs = await self.feedback_repo.get_by_user_id(user_id, limit=limit, offset=offset)
        return [Feedback.from_orm(obj) for obj in db_objs]

    async def get_by_opportunity_id(self, opportunity_id: int, limit: int = 100) -> List[Feedback]:
        """Get feedback by opportunity ID"""
        db_objs = await self.feedback_repo.get_by_opportunity_id(opportunity_id, limit=limit)
        return [Feedback.from_orm(obj) for obj in db_objs]

    async def update(self, db_obj: Feedback, obj_in: FeedbackUpdate) -> Feedback:
        """Update feedback"""
        # Convert to ORM object for repository
        from app.models import Feedback as FeedbackModel
        # Assuming we have the ORM object; if not, we need to fetch it
        # For simplicity, we expect db_obj to be an ORM instance or we fetch it
        if isinstance(db_obj, Feedback):
            # Convert schema to ORM object
            db_obj = FeedbackModel.from_orm(db_obj)
        updated_obj = await self.feedback_repo.update(db_obj, obj_in)
        return Feedback.from_orm(updated_obj)

    async def delete(self, id: int) -> Optional[Feedback]:
        """Delete feedback"""
        db_obj = await self.feedback_repo.delete(id)
        return Feedback.from_orm(db_obj) if db_obj else None