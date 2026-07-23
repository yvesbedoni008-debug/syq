#!/usr/bin/env python3
"""
Database initialization script
Creates tables and adds initial data if needed
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models import User
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db() -> None:
    """Initialize database with tables and optional seed data"""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Create a superuser if it doesn't exist
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            logger.info("Created admin user: admin@example.com")
        else:
            logger.info("Admin user already exists")

async def main():
    await init_db()

if __name__ == "__main__":
    asyncio.run(main())