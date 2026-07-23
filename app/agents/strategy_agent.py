"""Strategy Agent: formulates action recommendations based on analysis from other agents."""

from app.agents.base_agent import BaseAgent
from typing import Dict[Any, Any], Optional, List, Tuple
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyAgent(BaseAgent):
    """Agent responsible for synthesizing insights and recommending optimal actions."""

    def __init__(self):
        super().__init__("StrategyAgent")
        # Weights for different factors in decision making (should sum to 1.0)
        self.decision_weights = {
            "price": 0.20,      # Price value and fairness
            "trust": 0.20,      # Trustworthiness of seller/source
            "risk": 0.15,       # Risk level (inverted - lower risk is better)
            "market": 0.15,     # Market conditions and timing
            "personal": 0.15,   # Personal fit and preferences
            "discovery": 0.10   # How promising the opportunity itself is
        }

        # Action thresholds
        self.action_thresholds = {
            "strong_buy": 80,
            "buy": 65,
            "consider": 50,
            "weak_consider": 40,
            "avoid": 30,
            "strong_avoid": 20
        }

        # Market sentiment keywords for internal analysis
        self.bullish_indicators = [
            "high demand", "strong demand", "selling fast", "appreciating",
            "increasing value", "hot market", "seller's market", "competitive bidding",
            "multiple offers", "above asking", "bidding war", "limited inventory"
        ]

        self.bearish_indicators = [
            "low demand", "weak demand", "slow moving", "depreciating",
            "declining value", "buyer's market", "high inventory", "price reductions",
            "selling below asking", "long market time", "motivated sellers"
        ]

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate strategic recommendations based on opportunity data and agent insights.

        Expects context to contain analyses from other agents (discovery, market, price, trust, risk, personal).
        Returns recommended action (buy, wait, negotiate, avoid) and reasoning.
        """
        self._log_info("Processing strategy analysis")

        # Default values
        recommendation = "hold"  # hold, buy, negotiate, avoid, strong_avoid
        confidence = 0.6
        reasoning = []
        suggested_next_steps = []
        risk_warnings = []
        opportunity_highlights = []
        data_quality_indicators = []  # Track quality of data from underlying agents

        # Gather analyses from context if provided
        analyses = {}
        if context and isinstance(context, dict):
            # Expect keys like 'discovery', 'market', 'price', 'trust', 'risk', 'personal'
            for key in ["discovery", "market", "price", "trust", "risk", "personal"]:
                if key in context:
                    analyses[key] = context[key]

        # If no context provided, try to extract from opportunity_data directly (fallback)
        if not analyses:
            # Look for analysis results embedded in opportunity_data
            for key in ["discovery", "market", "price", "trust", "risk", "personal"]:
                if key in opportunity_data and isinstance(opportunity_data[key], dict):
                    analyses[key] = opportunity_data[key]

        # Extract scores with defaults and assess data quality
        price_analysis = analyses.get("price", {})
        price_score = price_analysis.get("price_score", 50)
        price_confidence = price_analysis.get("confidence", 0.7)

        trust_analysis = analyses.get("trust", {})
        trust_score = trust_analysis.get("trust_score", 50)
        trust_confidence = trust_analysis.get("confidence", 0.7)

        risk_analysis = analyses.get("risk", {})
        risk_score = risk_analysis.get("risk_score", 50)  # Higher = riskier
        risk_confidence = risk_analysis.get("confidence", 0.7)

        market_analysis = analyses.get("market", {})
        market_score = market_analysis.get("market_score", 50)
        market_confidence = market_analysis.get("confidence", 0.7)

        personal_analysis = analyses.get("personal", {})
        personal_score = personal_analysis.get("personal_score", 50)
        personal_confidence = personal_analysis.get("confidence", 0.7)

        discovery_analysis = analyses.get("discovery", {})
        discovery_score = discovery_analysis.get("discovery_score", 50)
        discovery_confidence = discovery_analysis.get("confidence", 0.7)

        # Assess overall data quality - if agents are using internal data (not phia), we still have good confidence
        # Since all agents now use internal implementations, we can have confidence in the data
        avg_confidence = (price_confidence + trust_confidence + risk_confidence +
                         market_confidence + personal_confidence + discovery_confidence) / 6
        # With internal implementations, we consider this reliable data
        using_internal_data = avg_confidence > 0.6  # Adjusted threshold for internal data

        if using_internal_data:
            data_quality_indicators.append("Analysis based on internal data models")
            confidence_base = 0.8  # Start with higher confidence when using internal data
        else:
            data_quality_indicators.append("Analysis may include limited or fallback data")
            confidence_base = 0.6  # Standard confidence

        # Convert risk score to inverse (since lower risk is better)
        risk_inverse = 100 - risk_score

        # Calculate weighted composite score
        weighted_score = (
            self.decision_weights["price"] * price_score +
            self.decision_weights["trust"] * trust_score +
            self.decision_weights["risk"] * risk_inverse +
            self.decision_weights["market"] * market_score +
            self.decision_weights["personal"] * personal_score +
            self.decision_weights["discovery"] * discovery_score
        )

        # Determine base recommendation
        if weighted_score >= self.action_thresholds["strong_buy"]:
            base_recommendation = "strong_buy"
            confidence_base = min(0.95, confidence_base + 0.1)  # Boost confidence for strong signals
        elif weighted_score >= self.action_thresholds["buy"]:
            base_recommendation = "buy"
            confidence_base = min(0.9, confidence_base + 0.05)
        elif weighted_score >= self.action_thresholds["consider"]:
            base_recommendation = "consider"
        elif weighted_score >= self.action_thresholds["weak_consider"]:
            base_recommendation = "weak_consider"
        elif weighted_score >= self.action_thresholds["avoid"]:
            base_recommendation = "avoid"
        else:
            base_recommendation = "strong_avoid"

        # Get additional market insight from internal analysis
        market_sentiment = self._get_market_sentiment_internal(opportunity_data, market_analysis)
        if market_sentiment:
            reasoning.append(f"Overall market sentiment: {market_sentiment}")
            # Adjust recommendation slightly based on market sentiment
            if market_sentiment == "strongly_bullish" and weighted_score >= 40:
                if base_recommendation in ["avoid", "strong_avoid"]:
                    base_recommendation = "consider"
                    opportunity_highlights.append("Strongly bullish market may offset concerns")
            elif market_sentiment == "strongly_bearish" and weighted_score <= 70:
                if base_recommendation in ["buy", "strong_buy"]:
                    base_recommendation = "consider"
                    risk_warnings.append("Strongly bearish market suggests caution")

        # Adjust recommendation based on specific risk factors
        risk_level = risk_analysis.get("risk_level", "moderate")
        risk_flags = risk_analysis.get("risk_factors", [])

        # Check for deal-breaker risks
        deal_breakers = [
            "scam", "fraud", "stolen", "counterfeit", "fake", "no title",
            "wire transfer only", "gift card", "extremely low price",
            "price <30% of market", "avoid platform protection"
        ]

        has_deal_breaker = any(
            any(term in str(flag).lower() for term in deal_breakers)
            for flag in risk_flags
        )

        # Check for strong positive signals
        strong_positives = [
            "excellent value", "below market", "verified identity",
            "escrow available", "service records", "clean title",
            "price <50% market", "luxury brand verified"
        ]

        has_strong_positive = any(
            any(term in str(detail).lower() for term in strong_positives)
            for detail in risk_analysis.get("risk_details", [])
        ) or any(
            any(term in str(detail).lower() for term in ["below market", "good value"])
            for detail in price_analysis.get("notes", "").split(";")
        )

        # Apply risk-based adjustments to recommendation
        if has_deal_breaker:
            # Override to avoid regardless of score
            base_recommendation = "strong_avoid"
            confidence_base = max(confidence_base, 0.85)
            risk_warnings.append("Deal-breaker risk detected - strong avoidance recommended")
        elif risk_level == "critical":
            base_recommendation = "strong_avoid"
            confidence_base = max(confidence_base, 0.8)
            risk_warnings.append("Critical risk level - avoid unless extraordinary verification possible")
        elif risk_level == "high" and weighted_score < 70:
            # Only downgrade if not already a strong buy
            if base_recommendation in ["strong_buy", "buy"]:
                base_recommendation = "consider"
                confidence_base = min(confidence_base, 0.65)
                risk_warnings.append("High risk tempers enthusiasm despite positive factors")
        elif risk_level == "low" and weighted_score > 50:
            # Slightly boost confidence for low-risk opportunities
            confidence_base = min(0.95, confidence_base + 0.05)

        # Check for exceptional value that might outweigh moderate risks
        if (weighted_score >= 70 and
            risk_level in ["moderate", "high"] and
            price_score >= 75 and
            not has_deal_breaker):
            # Exceptional deal might warrant consideration despite risks
            if base_recommendation == "avoid":
                base_recommendation = "consider"
                confidence_base = 0.6
                opportunity_highlights.append("Exceptional value may justify careful consideration despite risks")

        # Finalize recommendation
        recommendation = base_recommendation
        confidence = min(0.95, max(0.3, confidence_base))  # Clamp between 0.3 and 0.95

        # Build detailed reasoning
        reasoning.append(f"Composite score: {weighted_score:.1f}/100")
        reasoning.append(f"Price score: {price_score:.1f} (weight: {self.decision_weights['price']*100:.0f}%, confidence: {price_confidence:.0%})")
        reasoning.append(f"Trust score: {trust_score:.1f} (weight: {self.decision_weights['trust']*100:.0f}%, confidence: {trust_confidence:.0%})")
        reasoning.append(f"Risk score: {risk_score:.1f} -> {risk_inverse:.1f} safety (weight: {self.decision_weights['risk']*100:.0f}%, confidence: {risk_confidence:.0%})")
        reasoning.append(f"Market score: {market_score:.1f} (weight: {self.decision_weights['market']*100:.0f}%, confidence: {market_confidence:.0%})")
        reasoning.append(f"Personal score: {personal_score:.1f} (weight: {self.decision_weights['personal']*100:.0f}%, confidence: {personal_confidence:.0%})")
        reasoning.append(f"Discovery score: {discovery_score:.1f} (weight: {self.decision_weights['discovery']*100:.0f}%, confidence: {discovery_confidence:.0%})")

        # Add specific insights from analyses
        reasoning.append(f"Data quality: {'Internal data models' if using_internal_data else 'Limited or fallback data'}")
        for indicator in data_quality_indicators:
            reasoning.append(f"  - {indicator}")

        # Add key insights from each agent
        for key, analysis in analyses.items():
            if isinstance(analysis, dict) and "insights" in analysis:
                for insight in analysis["insights"][:2]:  # Limit to 2 insights per agent
                    reasoning.append(f"  - {key.title()}: {insight}")

        # Generate suggestions based on recommendation
        suggestions = self._generate_strategy_suggestions(recommendation, analyses, using_internal_data)
        suggested_next_steps.extend(suggestions)

        return {
            "agent": self.agent_name,
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
            "weighted_score": round(weighted_score, 1),
            "risk_level": risk_level,
            "reasoning": reasoning,
            "suggested_next_steps": suggested_next_steps,
            "risk_warnings": risk_warnings,
            "opportunity_highlights": opportunity_highlights,
            "data_quality": {
                "using_internal_data": using_internal_data,
                "average_confidence": round(avg_confidence, 2),
                "agent_confidences": {
                    "price": round(price_confidence, 2),
                    "trust": round(trust_confidence, 2),
                    "risk": round(risk_confidence, 2),
                    "market": round(market_confidence, 2),
                    "personal": round(personal_confidence, 2),
                    "discovery": round(discovery_confidence, 2)
                }
            },
            "confidence_in_data": 0.85 if using_internal_data else 0.7  # Higher confidence when using internal data
        }

    def _get_market_sentiment_internal(self, opportunity_data: dict, market_analysis: dict) -> Optional[str]:
        """Get overall market sentiment using internal analysis."""
        try:
            category = opportunity_data.get("category", "")
            if not category:
                return None

            # Use market analysis data if available
            market_score = market_analysis.get("market_score", 50) if market_analysis else 50
            market_trend = market_analysis.get("market_trend", "stable") if market_analysis else "stable"
            demand_velocity = market_analysis.get("demand_velocity", "steady") if market_analysis else "steady"

            # Also check for seasonal factors
            seasonal_score = 0
            if market_analysis:
                # Extract seasonal contribution from notes if available
                notes = market_analysis.get("notes", "")
                if "peak season" in notes.lower():
                    seasonal_score += 10
                elif "low season" in notes.lower():
                    seasonal_score -= 10

            # Determine sentiment based on multiple factors
            sentiment_score = 0

            # Market score contribution (0-50 points)
            if market_score >= 70:
                sentiment_score += 25
            elif market_score >= 60:
                sentiment_score += 15
            elif market_score >= 40:
                sentiment_score += 5
            elif market_score <= 30:
                sentiment_score -= 15
            elif market_score <= 20:
                sentiment_score -= 25

            # Market trend contribution (0-20 points)
            if market_trend == "strongly_rising":
                sentiment_score += 20
            elif market_trend == "rising":
                sentiment_score += 10
            elif market_trend == "declining":
                sentiment_score -= 10
            elif market_trend == "strongly_declining":
                sentiment_score -= 20

            # Demand velocity contribution (0-15 points)
            if demand_velocity == "high":
                sentiment_score += 15
            elif demand_velocity == "above_average":
                sentiment_score += 8
            elif demand_velocity == "below_average":
                sentiment_score -= 8
            elif demand_velocity == "low":
                sentiment_score -= 15

            # Seasonal contribution (0-10 points)
            sentiment_score += seasonal_score

            # Additional checks = sentiment_score
            if sentiment >= 30:
                return "strongly_bullish"
            elif sentiment >= 10:
                return "moderately_bullish"
            elif sentiment >= -10:
                return "neutral"
            elif sentiment >= -30:
                return "moderately_bearish"
            else:
                return "strongly_bearish"

        except Exception as e:
            self._log_debug(f"Could not compute internal market sentiment: {e}")
            return None  # Fallback to no sentiment adjustment

    def _generate_strategy_suggestions(self, recommendation: str, analyses: dict, using_internal_data: bool) -> list:
        """Generate actionable suggestions based on the strategic recommendation."""
        suggestions = []

        if recommendation == "strong_buy":
            suggestions.extend([
                "Proceed with confidence - strong opportunity across multiple dimensions",
                "Consider closing quickly as such opportunities may not last",
                "Use standard due diligence procedures"
            ])
            if using_internal_data:
                suggestions.append("Confidence heightened by internal data validation")
        elif recommendation == "buy":
            suggestions.extend([
                "Proceed with purchase - favorable risk/reward profile",
                "Perform standard verification steps",
                "Consider negotiating for better terms if possible"
            ])
            if using_internal_data:
                suggestions.append("Recommendation backed by internal market analytics")
        elif recommendation == "consider":
            suggestions.extend([
                "Worth further investigation before deciding",
                "Focus on verifying the most uncertain aspects",
                "Consider a trial or smaller commitment first if possible"
            ])
        elif recommendation == "weak_consider":
            suggestions.extend([
                "Proceed with caution - significant drawbacks present",
                "Require substantial concessions or guarantees",
                "Only proceed if able to mitigate key risks"
            ])
        elif recommendation == "avoid":
            suggestions.extend([
                "Not recommended - risks outweigh potential benefits",
                "Look for better alternatives",
                "Only consider if able to substantially mitigate major risks"
            ])
        elif recommendation == "strong_avoid":
            suggestions.extend([
                "Strongly advise against - high probability of negative outcome",
                "Do not proceed under current circumstances",
                "Look for substantially better alternatives"
            ])

        # Add specific suggestions based on analysis weaknesses
        if "trust" in analyses and analyses["trust"].get("trust_score", 50) < 40:
            suggestions.append("Require third-party verification before proceeding")

        if "price" in analyses and analyses["price"].get("price_score", 50) < 40:
            suggestions.append("Price appears unfavorable - negotiate or walk away")

        if "risk" in analyses and analyses["risk"].get("risk_score", 50) > 60:
            suggestions.append("Significant risks identified - require mitigation before proceeding")

        if "market" in analyses and analyses["market"].get("market_score", 50) < 40:
            suggestions.append("Unfavorable market conditions - consider timing")

        # Add data quality specific suggestions
        if not using_internal_data:
            suggestions.append("Consider verifying critical information through additional channels due to potential data limitations")

        return suggestions[:5]  # Limit to top 5 suggestions