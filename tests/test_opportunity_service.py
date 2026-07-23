"""
Test for Opportunity Service
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Opportunity
from app.core.database import Base
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.services import OpportunityService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture
async def db():
    """Create a fresh database for each test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_opportunity(db: AsyncSession):
    """Test creating an opportunity"""
    opportunity_service = OpportunityService(db)

    opportunity_data = {
        "title": "Test Opportunity",
        "description": "A test opportunity",
        "category": "Test",
        "source": "Test Source",
        "price": 10000,
        "market_value": 12000
    }

    opportunity = Opportunity(**opportunity_data)
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)

    assert opportunity.id is not None
    assert opportunity.title == "Test Opportunity"
    assert opportunity.price == 10000

@pytest.mark.asyncio
async def test_calculate_opportunity_score(db: AsyncSession):
    """Test calculating SYQ Score for an opportunity"""
    opportunity_service = OpportunityService(db)

    # Create test opportunity
    opportunity = Opportunity(
        title="Test Car",
        description="A test vehicle",
        category="Automotive",
        source="Test Dealer",
        price=20000,  # $20,000
        market_value=25000  # $25,000 market value
    )
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)

    # Calculate score
    score = await opportunity_service.calculate_opportunity_score(opportunity.id)

    assert score is not None
    assert score.opportunity_id == opportunity.id
    assert score.overall_score >= 0 and score.overall_score <= 100
    assert score.value_score >= 0 and score.value_score <= 100
    # With price at 80% of market value, we expect a good value score
    assert score.value_score > 50  # Should be favorable

if __name__ == "__main__":
    pytest.main([__file__, "-v"])