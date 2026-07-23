"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

class UserProfileBase(BaseModel):
    interests: Optional[str] = None
    preferences: Optional[str] = None
    risk_profile: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_categories: Optional[str] = None
    decision_weights: Optional[str] = None
    behavioral_patterns: Optional[str] = None
    risk_tolerance_history: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    user_id: int


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Opportunity
# ---------------------------------------------------------------------------

class OpportunityBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    price: Optional[int] = None
    market_value: Optional[int] = None
    status: Optional[str] = "active"


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    price: Optional[int] = None
    market_value: Optional[int] = None
    status: Optional[str] = None


class OpportunityInDBBase(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Opportunity(OpportunityInDBBase):
    pass


# ---------------------------------------------------------------------------
# Opportunity score
# ---------------------------------------------------------------------------

class OpportunityScoreBase(BaseModel):
    overall_score: Optional[int] = None
    value_score: Optional[int] = None
    price_score: Optional[int] = None
    demand_score: Optional[int] = None
    market_score: Optional[int] = None
    risk_score: Optional[int] = None
    confidence_score: Optional[int] = None
    explanation: Optional[str] = None


class OpportunityScoreCreate(OpportunityScoreBase):
    opportunity_id: int


class OpportunityScoreUpdate(OpportunityScoreBase):
    pass


class OpportunityScore(OpportunityScoreBase):
    id: int
    opportunity_id: int
    calculated_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

class MissionBase(BaseModel):
    goal: str
    constraints: Optional[str] = None
    priorities: Optional[Dict[str, float]] = None
    action_boundaries: Optional[Dict[str, List[str]]] = None
    approval_rules: Optional[Dict[str, Any]] = None
    status: Optional[str] = "active"
    version_number: Optional[int] = 1
    is_active: Optional[bool] = True
    frequency_min_minutes: Optional[int] = 30
    frequency_max_minutes: Optional[int] = 360
    current_frequency_minutes: Optional[int] = 60


class MissionCreate(MissionBase):
    user_id: int


class MissionUpdate(BaseModel):
    goal: Optional[str] = None
    constraints: Optional[str] = None
    priorities: Optional[Dict[str, float]] = None
    action_boundaries: Optional[Dict[str, List[str]]] = None
    approval_rules: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    frequency_min_minutes: Optional[int] = None
    frequency_max_minutes: Optional[int] = None
    current_frequency_minutes: Optional[int] = None
    change_reason: Optional[str] = None


class MissionInDBBase(MissionBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Mission(MissionInDBBase):
    pass


class MissionVersionBase(BaseModel):
    version_number: int
    goal: str
    constraints: Optional[str] = None
    priorities: Optional[Dict[str, float]] = None
    action_boundaries: Optional[Dict[str, List[str]]] = None
    approval_rules: Optional[Dict[str, Any]] = None
    changed_fields: Optional[str] = None
    change_reason: Optional[str] = None


class MissionVersionCreate(MissionVersionBase):
    mission_id: int
    created_by: int


class MissionVersionInDBBase(MissionVersionBase):
    id: int
    mission_id: int
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class MissionVersion(MissionVersionInDBBase):
    pass


# ---------------------------------------------------------------------------
# Trust signal
# ---------------------------------------------------------------------------

class TrustSignalBase(BaseModel):
    type: str
    severity: str
    explanation: Optional[str] = None


class TrustSignalCreate(TrustSignalBase):
    opportunity_id: int


class TrustSignalUpdate(BaseModel):
    type: Optional[str] = None
    severity: Optional[str] = None
    explanation: Optional[str] = None


class TrustSignal(TrustSignalBase):
    id: int
    opportunity_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackBase(BaseModel):
    outcome: str
    rating: Optional[int] = None
    profit_amount: Optional[int] = None
    feedback_text: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    user_id: int
    opportunity_id: int


class FeedbackUpdate(BaseModel):
    outcome: Optional[str] = None
    rating: Optional[int] = None
    profit_amount: Optional[int] = None
    feedback_text: Optional[str] = None


class Feedback(FeedbackBase):
    id: int
    user_id: int
    opportunity_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Search / intent
# ---------------------------------------------------------------------------

class IntentRequest(BaseModel):
    query: str


class OpportunityExplanation(BaseModel):
    opportunity_id: int
    title: str
    relevance_score: float
    explanation: str


class IntentResponse(BaseModel):
    query: str
    results: List[OpportunityExplanation]
    total: int
