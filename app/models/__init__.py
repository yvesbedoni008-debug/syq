"""Database models for SQLAlchemy"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Enum, Table, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# Association tables for opportunity relationships
opportunity_similarity = Table(
    'opportunity_similarity',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('similar_opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('similarity_score', Float),  # 0.0 to 1.0
    Column('similarity_type', String(50)),  # e.g., 'model', 'features', 'price_range', 'category'
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

opportunity_relationship = Table(
    'opportunity_relationship',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('related_opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('relationship_type', String(50)),  # e.g., 'substitute', 'complement', 'newer_model', 'older_model'
    Column('strength', Float),  # 0.0 to 1.0
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

opportunity_user_interest = Table(
    'opportunity_user_interest',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('interest_level', Integer),  # 0-100
    Column('saved_at', DateTime(timezone=True), server_default=func.now()),
    Column('last_viewed', DateTime(timezone=True), onupdate=func.now())
)

# Mission version table for tracking mission evolution
mission_version = Table(
    'mission_version',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('mission_id', Integer, ForeignKey('missions.id')),
    Column('version_number', Integer, nullable=False),
    Column('goal', String(255), nullable=False),
    Column('constraints', Text),
    Column('priorities', JSON),  # Weights for different dimensions
    Column('action_boundaries', JSON),  # What actions can be auto-prepared
    Column('approval_rules', JSON),  # When to auto-alert vs require human approval
    Column('changed_fields', JSON),  # What changed from previous version
    Column('change_reason', Text),  # Why the change was made
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('created_by', Integer, ForeignKey('users.id'))  # Who made the change
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    missions = relationship("Mission", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    interested_opportunities = relationship("Opportunity", secondary=opportunity_user_interest, back_populates="interested_users")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    interests = Column(Text)  # JSON string or comma-separated
    preferences = Column(Text)  # JSON string for structured preferences
    risk_profile = Column(String(50))  # conservative, moderate, aggressive
    budget_min = Column(Integer, nullable=True)
    budget_max = Column(Integer, nullable=True)
    preferred_categories = Column(Text)  # JSON array or comma-separated
    # Enhanced personalization fields
    decision_weights = Column(Text)  # JSON: weights for different decision factors (price, quality, brand, etc.)
    behavioral_patterns = Column(Text)  # JSON: historical decision patterns
    risk_tolerance_history = Column(Text)  # JSON: track record of risk vs reward outcomes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")


class OpportunityStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    INACTIVE = "inactive"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    source = Column(String(100))  # Where the opportunity came from
    price = Column(Integer)  # Current price
    market_value = Column(Integer)  # Estimated market value
    status = Column(String(20), default=OpportunityStatusEnum.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scores = relationship("OpportunityScore", back_populates="opportunity", cascade="all, delete-orphan")
    trust_signals = relationship("TrustSignal", back_populates="opportunity", cascade="all, delete-orphan")
    missions = relationship("MissionOpportunity", back_populates="opportunity")
    # Relationship graph connections
    similar_opportunities = relationship(
        "Opportunity",
        secondary=opportunity_similarity,
        primaryjoin=id==opportunity_similarity.c.opportunity_id,
        secondaryjoin=id==opportunity_similarity.c.similar_opportunity_id,
        backref="similar_to"
    )
    related_opportunities = relationship(
        "Opportunity",
        secondary=opportunity_relationship,
        primaryjoin=id==opportunity_relationship.c.opportunity_id,
        secondaryjoin=id==opportunity_relationship.c.related_opportunity_id,
        backref="related_from"
    )
    feedbacks = relationship("Feedback", back_populates="opportunity")
    interested_users = relationship(
        "User",
        secondary=opportunity_user_interest,
        back_populates="interested_opportunities"
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    overall_score = Column(Integer)  # 0-100
    value_score = Column(Integer)  # 0-100
    price_score = Column(Integer)  # 0-100
    demand_score = Column(Integer)  # 0-100
    market_score = Column(Integer)  # 0-100
    risk_score = Column(Integer)  # 0-100 (lower is better risk)
    confidence_score = Column(Integer)  # 0-100
    # Enhanced scoring components for better explainability
    value_explanation = Column(Text)
    price_explanation = Column(Text)
    demand_explanation = Column(Text)
    market_explanation = Column(Text)
    risk_explanation = Column(Text)
    confidence_explanation = Column(Text)
    # Contextual fields
    market_trend = Column(String(50))  # e.g., 'rising', 'falling', 'stable'
    scarcity_indicator = Column(String(50))  # e.g., 'limited', 'abundant', 'scarce'
    demand_velocity = Column(String(50))  # e.g., 'increasing', 'decreasing', 'steady'
    price_trend = Column(String(50))  # e.g., 'increasing', 'decreasing', 'stable'
    explanation = Column(Text)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    opportunity = relationship("Opportunity", back_populates="scores")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal = Column(String(255), nullable=False)
    constraints = Column(Text)  # JSON string containing structured constraints
    priorities = Column(JSON)  # Weights for different dimensions (trust, value, risk, etc.)
    action_boundaries = Column(JSON)  # What actions can be auto-prepared vs need approval
    approval_rules = Column(JSON)  # When to auto-alert vs require human approval
    status = Column(String(50), default="active")
    version_number = Column(Integer, default=1)  # Current version of the mission
    is_active = Column(Boolean, default=True)
    # Adaptive frequency settings
    frequency_min_minutes = Column(Integer, default=30)  # Minimum time between checks
    frequency_max_minutes = Column(Integer, default=360)  # Maximum time between checks
    current_frequency_minutes = Column(Integer, default=60)  # Current check interval
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="missions")
    opportunities = relationship("MissionOpportunity", back_populates="mission")
    versions = relationship("MissionVersion", back_populates="mission", cascade="all, delete-orphan")


class MissionVersion(Base):
    __tablename__ = "mission_versions"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    goal = Column(String(255), nullable=False)
    constraints = Column(Text)  # JSON string containing structured constraints
    priorities = Column(JSON)  # Weights for different dimensions
    action_boundaries = Column(JSON)  # What actions can be auto-prepared vs need approval
    approval_rules = Column(JSON)  # When to auto-alert vs require human approval
    changed_fields = Column(JSON)  # What changed from previous version
    change_reason = Column(Text)  # Why the change was made
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey('users.id'))  # Who made the change

    # Relationships
    mission = relationship("Mission", back_populates="versions")
    creator = relationship("User")


class TrustSignalTypeEnum(str, enum.Enum):
    SELLER_RELIABILITY = "seller_reliability"
    DATA_CONFIDENCE = "data_confidence"
    MARKET_ANOMALY = "market_anomaly"
    PRICE_ANOMALY = "price_anomaly"
    FRAUD_RISK = "fraud_risk"


class TrustSignal(Base):
    __tablename__ = "trust_signals"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    type = Column(String(50), nullable=False)  # From TrustSignalTypeEnum
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    opportunity = relationship("Opportunity", back_populates="trust_signals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    action = Column(String(100), nullable=False)  # e.g., "login", "create_opportunity", "score_calculation"
    resource_type = Column(String(50), nullable=True)  # e.g., "user", "opportunity", "mission"
    resource_id = Column(Integer, nullable=True)
    details = Column(Text)  # JSON string with additional context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class Feedback(Base):
    """User feedback on opportunities and outcomes for continuous learning"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    outcome = Column(String(50), nullable=False)  # e.g., 'success', 'failure', 'profit', 'loss'
    rating = Column(Integer, nullable=True)  # 1-5 scale for user satisfaction
    profit_amount = Column(Integer, nullable=True)  # Profit/Loss amount in currency units
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    opportunity = relationship("Opportunity", back_populates="feedbacks")