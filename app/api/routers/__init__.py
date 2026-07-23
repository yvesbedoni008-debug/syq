"""API Router for version 1 endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services import AuthService, UserService, OpportunityService, MissionService
from app.schemas import (
    UserCreate, User, UserUpdate, UserProfileCreate, UserProfileUpdate,
    Token, LoginRequest,
    OpportunityCreate, OpportunityUpdate,
    MissionCreate, MissionUpdate,
    OpportunityScore, TrustSignal,
    IntentRequest, OpportunityExplanation, IntentResponse
)
from app.models import OpportunityStatusEnum
from app.core.security import verify_token
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()


# Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user_service = UserService(db)
    user = await user_service.user_repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    return user


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Authentication Endpoints
@api_router.post("/register", response_model=dict)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)


@api_router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# User Endpoints
@api_router.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.get_user_profile(current_user.id)


@api_router.put("/users/me", response_model=dict)
async def update_user_me(
    user_in: UserUpdate,
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.update_user_profile(
        current_user.id, user_in, profile_in
    )


# Opportunity Endpoints
@api_router.get("/opportunities", response_model=dict)
async def read_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    status: Optional[OpportunityStatusEnum] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),  # Optional for public feed
    db: AsyncSession = Depends(get_db)
):
    opportunity_service = OpportunityService(db)
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if status:
        filters["status"] = status.value

    return await opportunity_service.get_opportunity_feed(
        user_id=current_user.id if current_user else None,
        skip=skip,
        limit=limit,
        filters=filters
    )


@api_router.get("/opportunities/{opportunity_id}", response_model=dict)
async def read_opportunity(
    opportunity_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    opportunity_service = OpportunityService(db)
    return await opportunity_service.get_opportunity_detail(
        opportunity_id=opportunity_id,
        user_id=current_user.id if current_user else None
    )


@api_router.post("/opportunities", response_model=Opportunity)
async def create_opportunity(
    opportunity_in: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # In a real implementation, only admins or specific roles could create opportunities
    opportunity_service = OpportunityService(db)
    opportunity = Opportunity(**opportunity_in.dict())
    # This would typically come from external data sources, not direct user input
    # For now, we're allowing it for demonstration
    return opportunity


# Search Endpoint
@api_router.post("/search", response_model=IntentResponse)
async def intent_search(
    intent_request: IntentRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # This would integrate with NLP services to parse the intent
    # For MVP, we'll implement a basic keyword-based approach
    opportunity_service = OpportunityService(db)

    # Parse intent (simplified for MVP)
    query_lower = intent_request.query.lower()

    # Extract basic filters from natural language
    filters = {}

    # Extract price constraints
    import re
    price_matches = re.findall(r'under\s*\$?(\d+)', query_lower)
    if price_matches:
        filters["max_price"] = int(price_matches[0])

    price_matches = re.findall(r'over\s*\$?(\d+)', query_lower)
    if price_matches:
        filters["min_price"] = int(price_matches[0])

    # Extract category hints
    categories = ["car", "vehicle", "auto", "automobile", "electronics", "phone", "laptop",
                 "furniture", "clothing", "jewelry", "watch", "real estate", "property"]
    for cat in categories:
        if cat in query_lower:
            filters["category"] = cat.capitalize()
            break

    # Get opportunities based on parsed intent
    opportunities_data = await opportunity_service.get_opportunity_feed(
        user_id=current_user.id if current_user else None,
        skip=0,
        limit=20,
        filters=filters
    )

    # Generate explanations for each opportunity
    explanations = []
    for opp_data in opportunities_data["opportunities"]:
        opportunity = opp_data["opportunity"]
        score = opp_data["score"]

        explanation = OpportunityExplanation(
            what_is_happening=f"Found {opportunity.title} in {opportunity.category or 'unspecified'} category",
            why_it_matters=f"This opportunity matches your search for '{intent_request.query}' with a SYQ Score of {score.overall_score if score else 'N/A'}",
            confidence_level="High" if score and score.confidence_score > 70 else "Medium" if score and score.confidence_score > 40 else "Low",
            risks=["Data may be incomplete"] if not score or score.confidence_score < 50 else [],
            considerations=[
                f"Price: ${opportunity.price}" if opportunity.price else "Price not specified",
                f"Market Value: ${opportunity.market_value}" if opportunity.market_value else "Market value not specified",
                f"Source: {opportunity.source}"
            ]
        )
        explanations.append(explanation)

    # Log the search
    audit_service = AuditLogRepository(db)
    await audit_service.create(
        action="intent_search",
        user_id=current_user.id if current_user else None,
        details=f"Search query: '{intent_request.query}' returned {len(opportunities_data['opportunities'])} results"
    )

    return IntentResponse(
        opportunities=[opp_data["opportunity"] for opp_data in opportunities_data["opportunities"]],
        explanations=explanations,
        query_interpretation={
            "original_query": intent_request.query,
            "parsed_filters": filters,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Mission Endpoints
@api_router.post("/missions", response_model=Mission)
async def create_mission(
    mission_in: MissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    mission_service = MissionService(db)
    return await mission_service.create_mission(current_user.id, mission_in)


@api_router.get("/missions", response_model=List[Mission])
async def read_user_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    mission_service = MissionService(db)
    return await mission_service.get_user_missions(current_user.id, skip=skip, limit=limit)


@api_router.put("/missions/{mission_id}", response_model=Mission)
async def update_mission(
    mission_id: int,
    mission_in: MissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    mission_service = MissionService(db)
    return await mission_service.update_mission(mission_id, mission_in, current_user.id)


# Health Check Endpoint
@api_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Simple database connectivity check
        await db.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )