"""Audit logging service"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import AuditLogRepository
from app.models import AuditLog
import json
import logging

logger = logging.getLogger(__name__)


class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditLogRepository(db)

    async def log_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log an action for audit trail"""
        try:
            # Serialize metadata if provided
            metadata_json = json.dumps(metadata) if metadata else None

            audit_log = await self.audit_repo.create(
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
                # Note: metadata would need to be added to AuditLog model if required
            )

            return audit_log
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            # Don't raise exception - auditing shouldn't break main functionality
            # In a production system, you might want to send to a dead letter queue
            raise

    async def get_user_activity(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """Get activity log for a specific user"""
        return await self.audit_repo.get_by_user_id(user_id, limit=limit, offset=offset)

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: int,
        limit: int = 50
    ) -> list:
        """Get history of actions on a specific resource"""
        return await self.audit_repo.get_by_resource(resource_type, resource_id, limit=limit)

    async def get_recent_actions(
        self,
        limit: int = 100,
        action_type: Optional[str] = None
    ) -> list:
        """Get recent actions across the system"""
        return await self.audit_repo.get_recent(limit=limit, action=action_type)