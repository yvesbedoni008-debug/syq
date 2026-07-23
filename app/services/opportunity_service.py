"""Enhanced opportunity service with improved scoring algorithm"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.repositories import (
    UserRepository, UserProfileRepository, OpportunityRepository,
    OpportunityScoreRepository, MissionRepository, TrustSignalRepository,
    AuditLogRepository
)
from app.agents.orchestrator import AgentOrchestrator
from app.schemas import (
    UserCreate, UserUpdate, UserProfileCreate, UserProfileUpdate,
    OpportunityCreate, OpportunityUpdate,
    OpportunityScoreCreate, OpportunityScoreUpdate,
    MissionCreate, MissionUpdate,
    TrustSignalCreate, TrustSignalUpdate
)
from app.core.security import create_access_token
from app.utils.redis import get_cached_score, set_cached_score, get_cached_agent_insights, set_cached_agent_insights, delete_cached_score, delete_cached_agent_insights
from datetime import timedelta
import logging
import math
import json

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> dict:
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create user
        user = await self.user_repo.create(user_in)

        # Create default profile
        profile_repo = UserProfileRepository(self.db)
        profile_in = UserProfileCreate(user_id=user.id)
        profile = await profile_repo.create(profile_in)

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        user = await self.user_repo.authenticate(email, password)
        if not user:
            return None

        # Log authentication attempt
        audit_repo = AuditLogRepository(self.db)
        await audit_repo.create(
            action="login",
            user_id=user.id,
            details=f"User {user.email} logged in"
        )

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            subject=user.email, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        user = await self.user_repo.get(user_id)
        if not user:
            return None

        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            # Create default profile if it doesn't exist
            profile_in = UserProfileCreate(user_id=user.id)
            profile = await self.profile_repo.create(profile_in)

        return {
            "user": user,
            "profile": profile
        }

    async def update_user_profile(
        self,
        user_id: int,
        user_in: UserUpdate,
        profile_in: UserProfileUpdate
    ) -> dict:
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        updated_user = await self.user_repo.update(user, user_in)
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            # Create profile if it doesn't exist
            profile_create = UserProfileCreate(user_id=user_id)
            profile = await self.profile_repo.create(profile_create)
        else:
            profile = await self.profile_repo.update(profile, profile_in)

        # Log the update
        await self.audit_repo.create(
            action="update_profile",
            user_id=user_id,
            details=f"User {user.email} updated profile"
        )

        return {
            "user": updated_user,
            "profile": profile
        }


class OpportunityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oppo_repo = OpportunityRepository(db)
        self.score_repo = OpportunityScoreRepository(db)
        self.trust_repo = TrustSignalRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.user_repo = UserRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.agent_orchestrator = AgentOrchestrator()

    async def get_opportunity_feed(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict] = None
    ) -> dict:
        opportunities = await self.oppo_repo.get_multi(
            skip=skip, limit=limit, filters=filters
        )

        # Get scores and trust signals for each opportunity
        results = []
        for opp in opportunities:
            score = await self.score_repo.get_by_opportunity_id(opp.id)
            trust_signals = await self.trust_repo.get_by_opportunity_id(opp.id)

            results.append({
                "opportunity": opp,
                "score": score,
                "trust_signals": trust_signals
            })

        # Log feed access if user_id provided
        if user_id:
            await self.audit_repo.create(
                action="view_feed",
                user_id=user_id,
                details=f"User viewed opportunity feed with {len(results)} items"
            )

        return {
            "opportunities": results,
            "total": len(results),
            "page": skip // limit + 1,
            "size": limit
        }

    async def get_opportunity_detail(
        self,
        opportunity_id: int,
        user_id: Optional[int] = None
    ) -> dict:
        opportunity = await self.oppo_repo.get(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        score = await self.score_repo.get_by_opportunity_id(opportunity_id)
        trust_signals = await self.trust_repo.get_by_opportunity_id(opportunity_id)

        # Log opportunity view
        if user_id:
            await self.audit_repo.create(
                action="view_opportunity",
                user_id=user_id,
                resource_type="opportunity",
                resource_id=opportunity_id,
                details=f"User viewed opportunity {opportunity.title}"
            )

        return {
            "opportunity": opportunity,
            "score": score,
            "trust_signals": trust_signals
        }

    async def get_agent_insights(
        self,
        opportunity_id: int,
        user_id: Optional[int] = None
    ) -> dict:
        """Get AI agent insights for an opportunity, running the full agent orchestrator.

        Returns a dictionary containing each agent's analysis and a synthesized recommendation.
        """
        # Try cache first
        cached = await get_cached_agent_insights(opportunity_id)
        if cached is not None:
            return cached

        opportunity = await self.oppo_repo.get(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        # Build user context if user_id provided
        user_context = {}
        if user_id:
            user = await self.user_repo.get(user_id)
            if user:
                profile = await self.profile_repo.get_by_user_id(user_id)
                user_context = {
                    "user_id": user.id,
                    "user_email": user.email,
                    "user_profile": {
                        "budget_min": getattr(profile, 'budget_min', None) if profile else None,
                        "budget_max": getattr(profile, 'budget_max', None) if profile else None,
                        "preferred_categories": getattr(profile, 'preferred_categories', None) if profile else None,
                        "risk_profile": getattr(profile, 'risk_profile', None) if profile else None,
                        "decision_weights": getattr(profile, 'decision_weights', None) if profile else None,
                        "behavioral_patterns": getattr(profile, 'behavioral_patterns', None) if profile else None,
                        "risk_tolerance_history": getattr(profile, 'risk_tolerance_history', None) if profile else None
                    }
                }

        # Convert opportunity to dict for agents
        opportunity_dict = {
            "id": opportunity.id,
            "title": opportunity.title,
            "description": opportunity.description,
            "category": opportunity.category,
            "source": opportunity.source,
            "price": opportunity.price,
            "market_value": opportunity.market_value,
            "status": opportunity.status,
            "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None,
            "updated_at": opportunity.updated_at.isoformat() if opportunity.updated_at else None
        }

        # Run the agent orchestrator
        orchestrator_result = await self.agent_orchestrator.run_agents(
            opportunity_data=opportunity_dict,
            user_context=user_context
        )

        # Cache the result (5 minute TTL)
        await set_cached_agent_insights(opportunity_id, orchestrator_result, expire=300)

        # Log the agent analysis (optional, could be verbose)
        await self.audit_repo.create(
            action="agent_analysis",
            user_id=user_id,
            resource_type="opportunity",
            resource_id=opportunity_id,
            details=f"Agent analysis completed for opportunity {opportunity.title}"
        )

        return orchestrator_result

    async def calculate_opportunity_score(self, opportunity_id: int) -> OpportunityScore:
        """Calculate enhanced SYQ Score for an opportunity with better algorithm"""
        # Try cache first
        cached_score_dict = await get_cached_score(opportunity_id)
        if cached_score_dict is not None:
            # Attempt to get existing score from DB; if not, create from cache
            existing_score = await self.score_repo.get_by_opportunity_id(opportunity_id)
            if existing_score:
                return existing_score
            # Create new score object from cached dict
            score_in = OpportunityScoreCreate(
                opportunity_id=opportunity_id,
                overall_score=cached_score_dict["overall_score"],
                value_score=cached_score_dict["value_score"],
                price_score=cached_score_dict["price_score"],
                demand_score=cached_score_dict["demand_score"],
                risk_score=cached_score_dict["risk_score"],
                confidence_score=cached_score_dict["confidence_score"],
                explanation=cached_score_dict["explanation"]
            )
            new_score = await self.score_repo.create(score_in)
            return new_score

        opportunity = await self.oppo_repo.get(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        # Get trust signals for risk calculation
        trust_signals = await self.trust_repo.get_by_opportunity_id(opportunity_id)

        # === VALUE SCORE (25% weight) ===
        # Measures how good the deal is compared to market value
        if opportunity.market_value and opportunity.market_value > 0:
            # Calculate discount/premium percentage
            discount_pct = (opportunity.market_value - opportunity.price) / opportunity.market_value

            # Convert to 0-100 score where:
            # - 50%+ discount = 100
            # - 0% discount (fair price) = 50
            # - 50%+ premium = 0
            if discount_pct >= 0.5:
                value_score = 100
            elif discount_pct <= -0.5:
                value_score = 0
            else:
                # Linear scale between -50% and +50%
                value_score = 50 + (discount_pct * 100)
        else:
            # No market value available - neutral score
            value_score = 50

        # === PRICE SCORE (20% weight) ===
        # Evaluates if price is competitive within category
        # For MVP, we'll use a simplified approach based on price history if available
        # In a real system, this would compare to similar items
        price_score = 50  # Default neutral

        # Simple heuristic: very low prices might be suspicious, very high might be overpriced
        if opportunity.price:
            # Assuming prices are in dollars (not cents) for this example
            price_in_dollars = opportunity.price

            # Very low prices (<$10) might indicate issues unless it's known to be cheap category
            # Very high prices (>$10000) need justification
            if price_in_dollars < 10 and opportunity.category not in ["Books", "Clothing", "Electronics Accessories"]:
                price_score = max(30, score - 20)  # Slightly suspicious
            elif price_in_dollars > 10000:
                score = max(30, score - 10)  # Needs justification for high price
            else:
                score = min(70, score + 10)  # Reasonable range gets slight boost

        # === DEMAND SCORE (20% weight) ===
        # Measures market interest and turnover speed
        # In a real system, this would use view counts, saves, time on market, etc.
        demand_score = 50  # Default

        # Simple heuristics based on available data
        if opportunity.description:
            desc_lower = opportunity.description.lower()
            # High demand indicators
            if any(word in desc_lower for word in ["popular", "trending", "in demand", "selling fast"]):
                demand_score = min(90, demand_score + 20)
            # Low demand indicators
            elif any(word in desc_lower for word in ["no longer needed", "must sell", "urgent", "price reduced"]):
                demand_score = max(20, demand_score - 15)  # Seller motivated but item may have issues

        # === MARKET SCORE (15% weight) ===
        # Evaluates supply/demand dynamics and competition
        market_score = 50  # Default

        # Simplified: items in certain categories might have better markets
        high_demand_categories = ["Electronics", "Vehicles", "Collectibles", "Luxury Goods"]
        if opportunity.category in high_demand_categories:
            market_score = min(80, market_score + 15)
        elif opportunity.category in ["Clothing", "Books", "Toys"]:
            # These can be oversaturated
            market_score = max(30, market_score - 10)

        # === RISK SCORE (15% weight) ===
        # Lower is better - we'll invert it for final calculation
        # Based on trust signals and listing quality
        risk_score = 0  # Start with no risk

        # Trust signal risks
        critical_signals = [ts for ts in trust_signals if getattr(ts, 'severity', '') == 'critical']
        high_signals = [ts for ts in trust_signals if getattr(ts, 'severity', '') == 'high']
        medium_signals = [ts for ts in trust_signals if getattr(ts, 'severity', '') == 'medium']

        risk_score += len(critical_signals) * 30  # Critical = big risk
        risk_score += len(high_signals) * 20      # High = significant risk
        risk_score += len(medium_signals) * 10    # Medium = moderate risk

        # Listing quality risks
        if not opportunity.description or len(opportunity.description) < 20:
            risk_score += 15  # Poor description
        if not opportunity.source or opportunity.source.lower() in ["unknown", "unspecified"]:
            risk_score += 10  # Unknown source

        # Cap risk score at 100
        risk_score = min(100, risk_score)

        # For final calculation, we invert risk (lower risk = higher score)
        # Risk score 0 -> 100 points, Risk score 100 -> 0 points
        risk_score_inverted = 100 - risk_score

        # === CONFIDENCE SCORE (10% weight) ===
        # Measures data quality and source reliability
        confidence_score = 50  # Base confidence

        # Data completeness
        if opportunity.title and len(opportunity.title) > 5:
            confidence_score += 10
        if opportunity.description and len(opportunity.description) > 50:
            confidence_score += 15
        if opportunity.source:
            confidence_score += 10
        if opportunity.price is not None:
            confidence_score += 10
        if opportunity.market_value is not None:
            confidence_score += 5

        # Source reliability (simplified)
        trusted_sources = ["Authorized Dealer", "Certified Refurbished", "Manufacturer",
                          "Official Store", "Reputable Marketplace"]
        if opportunity.source and any(trusted in opportunity.source for trusted in trusted_sources):
            confidence_score += 15

        # Cap at 100
        confidence_score = min(100, confidence_score)

        # === WEIGHTED OVERALL SCORE ===
        overall_score = int(
            value_score * 0.25 +        # 25% - Value (deal quality)
            price_score * 0.20 +        # 20% - Price competitiveness
            demand_score * 0.20 +       # 20% - Market demand
            (risk_score_inverted) * 0.15 + # 15% - Inverted risk (safety)
            confidence_score * 0.10     # 10% - Data confidence
        )

        # Ensure bounds
        overall_score = max(0, min(100, overall_score))

        # Generate detailed explanation
        explanation = self._generate_score_explanation(
            opportunity, value_score, price_score, demand_score,
            risk_score_inverted, confidence_score, overall_score, trust_signals
        )

        # Check if score already exists
        existing_score = await self.score_repo.get_by_opportunity_id(opportunity_id)
        if existing_score:
            score_in = OpportunityScoreUpdate(
                overall_score=max(0, min(100, overall_score)),
                value_score=max(0, min(100, value_score)),
                price_score=max(0, min(100, price_score)),
                demand_score=max(0, min(100, demand_score)),
                risk_score=max(0, min(100, risk_score)),  # Store actual risk score
                confidence_score=max(0, min(100, confidence_score)),
                explanation=explanation
            )
            updated_score = await self.score_repo.update(existing_score, score_in)
        else:
            score_in = OpportunityScoreCreate(
                opportunity_id=opportunity_id,
                overall_score=max(0, min(100, overall_score)),
                value_score=max(0, min(100, value_score)),
                price_score=max(0, min(100, price_score)),
                demand_score=max(0, min(100, demand_score)),
                risk_score=max(0, min(100, risk_score)),  # Store actual risk score
                confidence_score=max(0, min(100, confidence_score)),
                explanation=explanation
            )
            updated_score = await self.score_repo.create(score_in)

        # Cache the computed score (5 minute TTL)
        score_dict = {
            "overall_score": updated_score.overall_score,
            "value_score": updated_score.value_score,
            "price_score": updated_score.price_score,
            "demand_score": updated_score.demand_score,
            "risk_score": updated_score.risk_score,
            "confidence_score": updated_score.confidence_score,
            "explanation": updated_score.explanation
        }
        await set_cached_score(opportunity_id, score_dict, expire=300)

        # Log the score calculation
        await self.audit_repo.create(
            action="score_calculated",
            resource_type="opportunity",
            resource_id=opportunity_id,
            details=f"SYQ Score calculated: {overall_score}/100 (Value:{value_score} Price:{price_score} Demand:{demand_score} Risk:{risk_score} Conf:{confidence_score})"
        )

        return updated_score

    async def get_market_overview(self) -> dict:
        """Get overall market statistics and trends."""
        # Get counts per category, average price, price variance, etc.
        from sqlalchemy import func

        # Basic stats per category
        stmt = (
            select(
                Opportunity.category,
                func.count(Opportunity.id).label("opportunity_count"),
                func.avg(Opportunity.price).label("avg_price"),
                func.min(Opportunity.price).label("min_price"),
                func.max(Opportunity.price).label("max_price"),
                func.stddev(Opportunity.price).label("price_stddev")
            )
            .select_from(Opportunity)
            .group_by(Opportunity.category)
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()

        categories = []
        for row in rows:
            categories.append({
                "category": row.category,
                "opportunity_count": row.opportunity_count,
                "avg_price": float(row.avg_price) if row.avg_price is not None else 0.0,
                "min_price": float(row.min_price) if row.min_price is not None else 0.0,
                "max_price": float(row.max_price) if row.max_price is not None else 0.0,
                "price_stddev": float(row.price_stddev) if row.price_stddev is not None else 0.0
            })

        # Overall stats
        overall_stmt = (
            select(
                func.count(Opportunity.id).label("total_opportunities"),
                func.avg(Opportunity.price).label("overall_avg_price"),
                func.median(Opportunity.price).label("overall_median_price"),
                func.stddev(Opportunity.price).label("overall_price_stddev")
            )
            .select_from(Opportunity)
        )
        overall_result = await self.db.execute(overall_stmt)
        overall_row = overall_result.fetchone()

        # Simple trend indicator: proportion of opportunities with keywords indicating upward/downward momentum
        # This is a placeholder for more sophisticated trend detection
        trend_stmt = (
            select(
                func.count(Opportunity.id).label("total"),
                func.sum(
                    case(
                        (Opportunity.description.ilike('%trending up%') |
                         Opportunity.description.ilike('%increasing demand%') |
                         Opportunity.description.ilike('%rising%'), 1),
                        else_=0
                    )
                ).label("up_signals"),
                func.sum(
                    case(
                        (Opportunity.description.ilike('%trending down%') |
                         Opportunity.description.ilike('%declining%') |
                         Opportunity.description.ilike('%falling%'), 1),
                        else_=0
                    )
                ).label("down_signals")
            )
            .select_from(Opportunity)
        )
        # Note: case expression needs to be imported
        from sqlalchemy import case
        trend_result = await self.db.execute(
            select(
                func.count(Opportunity.id).label("total"),
                func.sum(
                    case(
                        (Opportunity.description.ilike('%trending up%') |
                         Opportunity.description.ilike('%increasing demand%') |
                         Opportunity.description.ilike('%rising%'), 1),
                        else_=0
                    )
                ).label("up_signals"),
                func.sum(
                    case(
                        (Opportunity.description.ilike('%trending down%') |
                         Opportunity.description.ilike('%declining%') |
                         Opportunity.description.ilike('%falling%'), 1),
                        else_=0
                    )
                ).label("down_signals")
            )
            .select_from(Opportunity)
        )
        trend_row = await self.db.execute(trend_stmt).fetchone()
        total = trend_row.total if trend_row else 0
        up = trend_row.up_signals if trend_row else 0
        down = trend_row.down_signals if trend_row else 0
        up_ratio = (up / total * 100) if total > 0 else 0
        down_ratio = (down / total * 100) if total > 0 else 0

        return {
            "categories": categories,
            "overall": {
                "total_opportunities": overall_row.total_opportunities if overall_row else 0,
                "avg_price": float(overall_row.overall_avg_price) if overall_row and overall_row.overall_avg_price is not None else 0.0,
                "median_price": float(overall_row.overall_median_price) if overall_row and overall_row.overall_median_price is not None else 0.0,
                "price_stddev": float(overall_row.overall_price_stddev) if overall_row and overall_row.overall_price_stddev is not None else 0.0
            },
            "trend_indicators": {
                "upward_momentum_percent": round(up_ratio, 2),
                "downward_momentum_percent": round(down_ratio, 2),
                "note": "Based on simple keyword detection in descriptions"
            }
        }

    def _generate_score_explanation(
        self,
        opportunity,
        value_score: float,
        price_score: float,
        demand_score: float,
        risk_score: float,  # This is the inverted risk score (safety)
        confidence_score: float,
        overall_score: float,
        trust_signals: list
    ) -> str:
        """Generate human-readable explanation of the score"""

        # Value explanation
        if opportunity.market_value and opportunity.market_value > 0:
            discount_pct = (opportunity.market_value - opportunity.price) / opportunity.market_value * 100
            if discount_pct > 20:
                value_desc = f"Excellent value - {discount_pct:.0f}% below market"
            elif discount_pct > 0:
                value_desc = f"Good value - {discount_pct:.0f}% below market"
            elif discount_pct > -20:
                value_desc = f"Fair market value - {abs(discount_pct):.0f}% above/below market"
            else:
                value_desc = f"Above market - {abs(discount_pct):.0f}% premium"
        else:
            value_desc = "Market value not available for comparison"

        # Risk explanation (using original risk score for clarity)
        actual_risk_score = 100 - risk_score  # Convert back to risk scale
        risk_factors = []
        if trust_signals:
            critical_count = len([ts for ts in trust_signals if getattr(ts, 'severity', '') == 'critical'])
            high_count = len([ts for ts in trust_signals if getattr(ts, 'severity', '') == 'high'])
            if critical_count > 0:
                risk_factors.append(f"{critical_count} critical risk flag{'s' if critical_count > 1 else ''}")
            if high_count > 0:
                risk_factors.append(f"{high_count} high risk flag{'s' if high_count > 1 else ''}")

        if not risk_factors:
            if actual_risk_score < 20:
                risk_desc = "Very low risk - listing appears reliable"
            elif actual_risk_score < 40:
                risk_desc = "Low risk - minor concerns only"
            elif actual_risk_score < 60:
                risk_desc = "Moderate risk - standard due diligence recommended"
            elif actual_risk_score < 80:
                risk_desc = "Elevated risk - exercise caution"
            else:
                risk_desc = "High risk - significant concerns identified"
        else:
            risk_desc = f"Risk factors detected: {', '.join(risk_factors)}"

        # Confidence explanation
        if confidence_score >= 80:
            desc = "High confidence - complete, reliable data from trusted sources"
        elif confidence_score >= 60:
            desc = "Good confidence - adequate data quality"
        elif confidence_score >= 40:
            desc = "Moderate confidence - some data limitations"
        else:
            desc = "Low confidence - limited or unverified information"

        # Build explanation
        explanation_parts = [
            f"SYQ Score {overall_score}/100:",
            f"• Value: {value_score}/100 ({value_desc})",
            f"• Price: {int(price_score)}/100 (competitive pricing assessment)",
            f"• Demand: {int(demand_score)}/100 (market interest level)",
            f"• Safety: {int(risk_score)}/100 ({risk_desc})",
            f"• Confidence: {int(confidence_score)}/100 ({desc})"
        ]

        return "\n".join(explanation_parts)

    async def _delete_opportunity_caches(self, opportunity_id: int) -> None:
        """Delete cached score and agent insights for an opportunity."""
        await delete_cached_score(opportunity_id)
        await delete_cached_agent_insights(opportunity_id)

    async def update_opportunity(
        self,
        opportunity_id: int,
        opportunity_in: OpportunityUpdate,
        user_id: Optional[int] = None
    ) -> Opportunity:
        """Update an opportunity and invalidate related caches."""
        opportunity = await self.oppo_repo.get(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        updated_opportunity = await self.oppo_repo.update(opportunity, opportunity_in)

        # Invalidate caches for this opportunity
        await self._delete_opportunity_caches(opportunity_id)

        # Log the update
        await self.audit_repo.create(
            action="update_opportunity",
            user_id=user_id,
            resource_type="opportunity",
            resource_id=opportunity_id,
            details=f"Opportunity '{opportunity.title}' updated"
        )

        return updated_opportunity

    async def delete_opportunity(
        self,
        opportunity_id: int,
        user_id: Optional[int] = None
    ) -> None:
        """Delete an opportunity and invalidate related caches."""
        opportunity = await self.oppo_repo.get(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        # Delete the opportunity
        await self.oppo_repo.delete(opportunity)

        # Invalidate caches for this opportunity
        await self._delete_opportunity_caches(opportunity_id)

        # Log the deletion
        await self.audit_repo.create(
            action="delete_opportunity",
            user_id=user_id,
            resource_type="opportunity",
            resource_id=opportunity_id,
            details=f"Opportunity '{opportunity.title}' deleted"
        )

    async def create_trust_signal(
        self,
        trust_signal_in: TrustSignalCreate,
        user_id: Optional[int] = None
    ) -> TrustSignal:
        """Create a trust signal and invalidate related opportunity caches."""
        trust_signal = await self.trust_repo.create(trust_signal_in)

        # Invalidate caches for the associated opportunity
        await self._delete_opportunity_caches(trust_signal.opportunity_id)

        # Log the creation
        await self.audit_repo.create(
            action="create_trust_signal",
            user_id=user_id,
            resource_type="trust_signal",
            resource_id=trust_signal.id,
            details=f"Trust signal created for opportunity {trust_signal.opportunity_id}"
        )

        return trust_signal

    async def update_trust_signal(
        self,
        trust_signal_id: int,
        trust_signal_in: TrustSignalUpdate,
        user_id: Optional[int] = None
    ) -> TrustSignal:
        """Update a trust signal and invalidate related opportunity caches."""
        trust_signal = await self.trust_repo.get(trust_signal_id)
        if not trust_signal:
            raise ValueError("Trust signal not found")

        updated_trust_signal = await self.trust_repo.update(trust_signal, trust_signal_in)

        # Invalidate caches for the associated opportunity
        await self._delete_opportunity_caches(updated_trust_signal.opportunity_id)

        # Log the update
        await self.audit_repo.create(
            action="update_trust_signal",
            user_id=user_id,
            resource_type="trust_signal",
            resource_id=trust_signal_id,
            details=f"Trust signal {trust_signal_id} updated"
        )

        return updated_trust_signal

    async def delete_trust_signal(
        self,
        trust_signal_id: int,
        user_id: Optional[int] = None
    ) -> None:
        """Delete a trust signal and invalidate related opportunity caches."""
        trust_signal = await self.trust_repo.get(trust_signal_id)
        if not trust_signal:
            raise ValueError("Trust signal not found")

        opportunity_id = trust_signal.opportunity_id

        # Delete the trust signal
        await self.trust_repo.delete(trust_signal)

        # Invalidate caches for the associated opportunity
        await self._delete_opportunity_caches(opportunity_id)

        # Log the deletion
        await self.audit_repo.create(
            action="delete_trust_signal",
            user_id=user_id,
            resource_type="trust_signal",
            resource_id=trust_signal_id,
            details=f"Trust signal {trust_signal_id} deleted"
        )