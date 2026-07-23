"""Trust signal API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import AuditLogService
from app.schemas import TrustSignalCreate, TrustSignalUpdate, TrustSignal
from app.core.security import get_current_user
from app.websocket.manager import manager

router = APIRouter()


@router.post("/", response_model=TrustSignal, status_code=status.HTTP_201_CREATED)
async def create_trust_signal(
    signal_in: TrustSignalCreate,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new trust signal for an opportunity."""
    from app.repositories import TrustSignalRepository
    from app.models import Opportunity

    # Verify opportunity exists and user has access (if needed)
    opportunity_repo = OpportunityRepository(db)
    opportunity = await opportunity_repo.get(signal_in.opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    # In a real app, you might check if the user has permission to add signals to this opportunity
    # For now, we'll allow any authenticated user to add trust signals

    trust_signal_repo = TrustSignalRepository(db)
    signal = await trust_signal_repo.create(signal_in)

    # Log the creation
    audit_service = AuditLogService(db)
    await audit_service.log_action(
        action="create_trust_signal",
        user_id=getattr(current_user, 'id', None) if current_user else None,
        resource_type="trust_signal",
        resource_id=signal.id,
        details=f"Trust signal created: {signal.type} - {signal.severity}"
    )

    # Broadcast real-time update for the opportunity
    await manager.broadcast({
        "type": "opportunity_updated",
        "opportunity_id": signal.opportunity_id
    })

    return signal


@router.get("/opportunity/{opportunity_id}", response_model=List[TrustSignal])
async def get_trust_signals_by_opportunity(
    opportunity_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all trust signals for a specific opportunity."""
    from app.repositories import TrustSignalRepository, OpportunityRepository

    # Verify opportunity exists
    opportunity_repo = OpportunityRepository(db)
    opportunity = await opportunity_repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    trust_signal_repo = TrustSignalRepository(db)
    signals = await trust_signal_repo.get_by_opportunity_id(opportunity_id)
    return signals


@router.put("/{signal_id}", response_model=TrustSignal)
async def update_trust_signal(
    signal_id: int,
    signal_in: TrustSignalUpdate,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing trust signal."""
    from app.repositories import TrustSignalRepository
    from app.models import TrustSignal

    trust_signal_repo = TrustSignalRepository(db)
    signal = await trust_signal_repo.get(signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust signal not found"
        )

    # In a real app, you might check ownership or permissions here

    update_data = signal_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(signal, field, value)

    await trust_signal_repo.db.commit()
    await trust_signal_repo.db.refresh(signal)

    # Log the update
    audit_service = AuditLogService(db)
    await audit_service.log_action(
        action="update_trust_signal",
        user_id=getattr(current_user, 'id', None) if current_user else None,
        resource_type="trust_signal",
        resource_id=signal_id,
        details=f"Trust signal updated: {signal.type}"
    )

    # Broadcast real-time update for the opportunity
    await manager.broadcast({
        "type": "opportunity_updated",
        "opportunity_id": signal.opportunity_id
    })

    return signal


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trust_signal(
    signal_id: int,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a trust signal."""
    from app.repositories import TrustSignalRepository

    trust_signal_repo = TrustSignalRepository(db)
    signal = await trust_signal_repo.get(signal_id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust signal not found"
        )

    # In a real app, you might check ownership or permissions here

    await trust_signal_repo.db.delete(signal)
    await trust_signal_repo.db.commit()

    # Log the deletion
    audit_service = AuditLogService(db)
    await audit_service.log_action(
        action="delete_trust_signal",
        user_id=getattr(current_user, 'id', None) if current_user else None,
        resource_type="trust_signal",
        resource_id=signal_id,
        details=f"Trust signal deleted: {signal.type}"
    )

    # Broadcast real-time update for the opportunity
    await manager.broadcast({
        "type": "opportunity_updated",
        "opportunity_id": signal.opportunity_id
    })

    return None