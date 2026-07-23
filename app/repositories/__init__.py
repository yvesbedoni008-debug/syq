"""Repository pattern for data access layer"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc
from app.models import (
    User, UserProfile, Opportunity, OpportunityScore,
    Mission, TrustSignal, AuditLog, Feedback,
    opportunity_similarity, opportunity_relationship, opportunity_user_interest
)
from app.schemas import (
    UserCreate, UserUpdate, UserProfileCreate, UserProfileUpdate,
    OpportunityCreate, OpportunityUpdate,
    OpportunityScoreCreate, OpportunityScoreUpdate,
    MissionCreate, MissionUpdate,
    TrustSignalCreate, TrustSignalUpdate,
    FeedbackCreate, FeedbackUpdate
)
from app.core.security import get_password_hash, verify_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(
            email=obj_in.email,
            password_hash=hashed_password,
            is_active=obj_in.is_active if hasattr(obj_in, 'is_active') else True
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(
                update_data.pop("password")
            )
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


class UserProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj_in: UserProfileCreate) -> UserProfile:
        db_obj = UserProfile(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: UserProfile, obj_in: UserProfileUpdate) -> UserProfile:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj


class OpportunityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[Opportunity]:
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        query = select(Opportunity)

        if filters:
            if "category" in filters:
                query = query.where(Opportunity.category == filters["category"])
            if "min_price" in filters:
                query = query.where(Opportunity.price >= filters["min_price"])
            if "max_price" in filters:
                query = query.where(Opportunity.price <= filters["max_price"])
            if "status" in filters:
                query = query.where(Opportunity.status == filters["status"])

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: OpportunityCreate) -> Opportunity:
        db_obj = Opportunity(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Opportunity, obj_in: OpportunityUpdate) -> Opportunity:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> Optional[Opportunity]:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj

    async def get_similar_opportunities(self, opportunity_id: int, limit: int = 10) -> List[Opportunity]:
        """Get opportunities similar to the given opportunity."""
        result = await self.db.execute(
            select(Opportunity)
            .join(
                opportunity_similarity,
                (opportunity_similarity.c.similar_opportunity_id == Opportunity.id)
                & (opportunity_similarity.c.opportunity_id == opportunity_id)
            )
            .order_by(opportunity_similarity.c.similarity_score.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_related_opportunities(self, opportunity_id: int, relationship_type: Optional[str] = None, limit: int = 10) -> List[Opportunity]:
        """Get opportunities related to the given opportunity."""
        query = select(Opportunity).join(
            opportunity_relationship,
            (opportunity_relationship.c.related_opportunity_id == Opportunity.id)
            & (opportunity_relationship.c.opportunity_id == opportunity_id)
        )
        if relationship_type:
            query = query.where(opportunity_relationship.c.relationship_type == relationship_type)
        query = query.order_by(opportunity_relationship.c.strength.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_interested_opportunities(self, user_id: int, limit: int = 10) -> List[Opportunity]:
        """Get opportunities that a user has shown interest in."""
        result = await self.db.execute(
            select(Opportunity)
            .join(
                opportunity_user_interest,
                (opportunity_user_interest.c.opportunity_id == Opportunity.id)
                & (opportunity_user_interest.c.user_id == user_id)
            )
            .order_by(opportunity_user_interest.c.interest_level.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def find_path_between_opportunities(self, source_id: int, target_id: int, max_depth: int = 3) -> List[List[int]]:
        """Find paths between two opportunities using similarity and relationship edges (simple BFS limited depth)."""
        # Fetch all edges (for MVP, we load all; in production, we'd limit or use graph traversal)
        similar_result = await self.db.execute(
            select(opportunity_similarity.c.opportunity_id, opportunity_similarity.c.similar_opportunity_id)
        )
        rel_result = await self.db.execute(
            select(opportunity_relationship.c.opportunity_id, opportunity_relationship.c.related_opportunity_id)
        )
        # Build undirected adjacency list
        adj = {}
        def add_edge(u, v):
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
        for row in similar_result:
            add_edge(row[0], row[1])
        for row in rel_result:
            add_edge(row[0], row[1])
        # BFS to find all shortest paths up to max_depth
        from collections import deque
        if source_id not in adj or target_id not in adj:
            return []
        queue = deque([(source_id, [source_id])])
        visited = {source_id: [source_id]}
        found_paths = []
        while queue:
            node, path = queue.popleft()
            if node == target_id:
                found_paths.append(path)
                continue
            if len(path) >= max_depth:
                continue
            for neigh in adj.get(node, []):
                if neigh not in visited or len(visited[neigh]) > len(path) + 1:
                    visited[neigh] = path + [neigh]
                    queue.append((neigh, path + [neigh]))
        return found_paths

    async def recommend_opportunities_for_user(self, user_id: int, limit: int = 10) -> List[Opportunity]:
        """Recommend opportunities for a user based on their interests and similarity."""
        # Get user's interacted opportunities
        interacted = await self.get_user_interested_opportunities(user_id, limit=5)
        if not interacted:
            # Fallback to general popular/recent opportunities
            return await self.get_multi(limit=limit)
        # Collect similar opportunities from each interacted opportunity
        similar_ids = set()
        for opp in interacted:
            sims = await self.get_similar_opportunities(opp.id, limit=5)
            for sim in sims:
                if sim.id != user_id:  # Avoid self-recommendation (though opportunity ID != user ID generally)
                    similar_ids.add(sim.id)
        # Also include the interacted opportunities themselves? Usually not, but we can if desired.
        # For now, we recommend similar ones, not the ones already interacted.
        if not similar_ids:
            return await self.get_multi(limit=limit)
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id.in_(list(similar_ids))).limit(limit)
        )
        return result.scalars().all()


class OpportunityScoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_opportunity_id(self, opportunity_id: int) -> Optional[OpportunityScore]:
        result = await self.db.execute(
            select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj_in: OpportunityScoreCreate) -> OpportunityScore:
        db_obj = OpportunityScore(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: OpportunityScore, obj_in: OpportunityScoreUpdate) -> OpportunityScore:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj


class MissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[Mission]:
        result = await self.db.execute(select(Mission).where(Mission.id == id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Mission]:
        result = await self.db.execute(
            select(Mission)
            .where(Mission.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: MissionCreate) -> Mission:
        db_obj = Mission(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Mission, obj_in: MissionUpdate) -> Mission:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj


class TrustSignalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[TrustSignal]:
        result = await self.db.execute(
            select(TrustSignal).where(TrustSignal.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_opportunity_id(self, opportunity_id: int) -> List[TrustSignal]:
        result = await self.db.execute(
            select(TrustSignal).where(TrustSignal.opportunity_id == opportunity_id)
        )
        return result.scalars().all()

    async def create(self, obj_in: TrustSignalCreate) -> TrustSignal:
        db_obj = TrustSignal(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def create_multiple(self, objs_in: List[TrustSignalCreate]) -> List[TrustSignal]:
        db_objs = [TrustSignal(**obj_in.dict()) for obj_in in objs_in]
        self.db.add_all(db_objs)
        await self.db.commit()
        for obj in db_objs:
            await self.db.refresh(obj)
        return db_objs

    async def delete_by_opportunity_id(self, opportunity_id: int) -> int:
        result = await self.db.execute(
            delete(TrustSignal).where(TrustSignal.opportunity_id == opportunity_id)
        )
        await self.db.commit()
        return result.rowcount


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        db_obj = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.resource_type == resource_type)
            .where(AuditLog.resource_id == resource_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent(
        self,
        limit: int = 100,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        if action is not None:
            query = query.where(AuditLog.action == action)
        result = await self.db.execute(query)
        return result.scalars().all()


class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[Feedback]:
        result = await self.db.execute(select(Feedback).where(Feedback.id == id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Feedback]:
        result = await self.db.execute(
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_opportunity_id(self, opportunity_id: int, limit: int = 100) -> List[Feedback]:
        result = await self.db.execute(
            select(Feedback)
            .where(Feedback.opportunity_id == opportunity_id)
            .order_by(Feedback.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: FeedbackCreate) -> Feedback:
        db_obj = Feedback(**obj_in.dict())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Feedback, obj_in: FeedbackUpdate) -> Feedback:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> Optional[Feedback]:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj