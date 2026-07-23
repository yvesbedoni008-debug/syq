"""Opportunity management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import OpportunityService, AuditLogService
from app.schemas import OpportunityCreate, OpportunityUpdate, Opportunity, OpportunityScore
from app.core.security import get_current_user
from app.models import OpportunityStatusEnum
from typing import Optional

router = APIRouter()


@router.get("/", response_model=dict)
async def read_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    status: Optional[OpportunityStatusEnum] = Query(None),
    current_user: Optional[object] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get opportunities feed with filtering and pagination"""
    opportunity_service = OpportunityService(db)
    audit_service = AuditLogService(db)
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if status:
        filters["status"] = status.value

    result = await opportunity_service.get_opportunity_feed(
        user_id=getattr(current_user, 'id', None) if current_user else None,
        skip=skip,
        limit=limit,
        filters=filters
    )

    # Log the feed access
    if current_user:
        await audit_service.log_action(
            action="view_feed",
            user_id=current_user.id,
            details=f"User viewed opportunity feed with {len(result['opportunities'])} items"
        )

    return result


@router.get("/{opportunity_id}", response_model=dict)
async def read_opportunity(
    opportunity_id: int,
    current_user: Optional[object] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific opportunity"""
    opportunity_service = OpportunityService(db)
    audit_service = AuditLogService(db)

    result = await opportunity_service.get_opportunity_detail(
        opportunity_id=opportunity_id,
        user_id=getattr(current_user, 'id', None) if current_user else None
    )

    # Log the opportunity view
    if current_user:
        opportunity = result["opportunity"]
        await audit_service.log_action(
            action="view_opportunity",
            user_id=current_user.id,
            resource_type="opportunity",
            resource_id=opportunity.id,
            details=f"User viewed opportunity: {opportunity.title}"
        )

    return result


@router.post("/", response_model=Opportunity)
async def create_opportunity(
    opportunity_in: OpportunityCreate,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new opportunity (typically done by external data sources)"""
    opportunity_service = OpportunityService(db)
    audit_service = AuditLogService(db)

    opportunity = Opportunity(**opportunity_in.dict())
    created_opportunity = await opportunity_service.oppo_repo.create(opportunity)

    # Log the creation
    await audit_service.log_action(
        action="create_opportunity",
        user_id=current_user.id,
        resource_type="opportunity",
        resource_id=created_opportunity.id,
        details=f"Opportunity created: {created_opportunity.title}"
    )

    return created_opportunity


@router.put("/{opportunity_id}", response_model=Opportunity)
async def update_opportunity(
    opportunity_id: int,
    opportunity_in: OpportunityUpdate,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an opportunity"""
    opportunity_service = OpportunityService(db)
    audit_service = AuditLogService(db)

    opportunity = await opportunity_service.oppo_repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # In production, add authorization checks here
    updated_opportunity = await opportunity_service.oppo_repo.update(opportunity, opportunity_in)

    # Log the update
    await audit_service.log_action(
        action="update_opportunity",
        user_id=current_user.id,
        resource_type="opportunity",
        resource_id=opportunity_id,
        details=f"Opportunity updated: {opportunity.title}"
    )

    return updated_opportunity


@router.get("/{opportunity_id}/score", response_model=OpportunityScore)
async def get_opportunity_score(
    opportunity_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get or calculate SYQ Score for an opportunity"""
    opportunity_service = OpportunityService(db)
    audit_service = AuditLogService(db)

    score = await opportunity_service.calculate_opportunity_score(opportunity_id)

    # Log the score calculation (optional, could be noisy)
    # await audit_service.log_action(
    #     action="calculate_score",
    #     user_id=current_user.id,
    #     resource_type="opportunity",
    #     resource_id=opportunity_id,
    #     details=f"SYQ Score calculated: {score.overall_score}/100"
    # )

    return score


@router.get("/{opportunity_id}/agents", response_model=dict)
async def get_opportunity_agent_insights(
    opportunity_id: int,
    current_user: Optional[object] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI agent insights for an opportunity."""
    opportunity_service = OpportunityService(db)
    # Pass current user id if available
    user_id = getattr(current_user, 'id', None) if current_user else None
    insights = await opportunity_service.get_agent_insights(
        opportunity_id=opportunity_id,
        user_id=user_id
    )
    return insights


@router.get("/market/overview", response_model=dict)
async def get_market_overview(
    current_user: Optional[object] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overall market overview and trends."""
    opportunity_service = OpportunityService(db)
    # Optionally could restrict to admins or allow any authenticated user
    overview = await opportunity_service.get_market_overview()
    return overview