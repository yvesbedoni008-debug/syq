"""Market Agent: analyzes market trends, demand patterns, pricing cycles."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import re
import math
import random

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """Agent responsible for analyzing market-level trends and demand."""

    def __init__(self):
        super().__init__("MarketAgent")
        # Keep some fallback data for internal analysis
        self.seasonal_patterns = {
            "electronics": {"peak_months": [11, 12, 1], "low_months": [2, 3, 4]},
            "clothing": {"peak_months": [3, 4, 9, 10], "low_months": [1, 7, 8]},
            "furniture": {"peak_months": [3, 4, 5, 9, 10], "low_months": [1, 2, 7, 8]},
            "vehicles": {"peak_months": [3, 4, 5, 9, 10], "low_months": [1, 2, 7, 8, 11, 12]},
            "real_estate": {"peak_months": [4, 5, 6, 7, 8, 9], "low_months": [1, 2, 11, 12]},
            "sports": {"peak_months": [4, 5, 6, 7, 8, 9], "low_months": [1, 2, 11, 12]},
        }

        # Category-specific growth trends (annual %)
        self.category_trends = {
            "electronics": -2.5,  # declining due to rapid obsolescence
            "computers": -5.0,
            "phones": -3.0,
            "home_appliances": 1.5,
            "furniture": 2.0,
            "collectibles": 5.0,
            "luxury_goods": 3.0,
            "vehcles": -1.5,
            "real_estate": 4.0,
            "sports_equipment": 1.0,
            "books": -3.0,
            "toys": 0.5
        }

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze market trends and demand for the opportunity.

        Returns market score, trend insights, and demand velocity.
        """
        self._log_info("Processing market analysis")

        # Initialize scores and factors
        market_score = 50  # Start neutral
        trend_factors = []
        demand_indicators = []
        notes = []

        # Extract relevant data
        category = opportunity_data.get("category", "").lower()
        price = opportunity_data.get("price")
        listed_date_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        location = opportunity_data.get("location", "").lower()
        title = opportunity_data.get("title", "").lower()
        description = opportunity_data.get("description", "").lower()

        # 1. Category Trend Analysis (internal)
        category_score, category_notes = self._analyze_category_trends_internal(category)
        market_score += category_score
        notes.extend(category_notes)

        # 2. Seasonal Analysis (internal)
        seasonal_score, seasonal_notes = self._analyze_seasonal_factors_internal(category, listed_date_str)
        market_score += seasonal_score
        notes.extend(seasonal_notes)

        # 3. Price Positioning Analysis (internal)
        price_score, price_notes = self._analyze_price_positioning_internal(category, price, title, description)
        market_score += price_score
        notes.extend(price_notes)

        # 4. Demand Velocity Indicators (internal)
        demand_score, demand_notes = self._analyze_demand_velocity_internal(opportunity_data)
        market_score += demand_score
        notes.extend(demand_notes)

        # 5. Geographic Market Factors (internal)
        geo_score, geo_notes = self._analyze_geographic_factors_internal(location, category)
        market_score += geo_score
        notes.extend(geo_notes)

        # Ensure score stays within bounds
        market_score = max(0, min(100, market_score))

        # Determine trend direction
        if market_score >= 70:
            market_trend = "strongly_rising"
            demand_velocity = "high"
        elif market_score >= 60:
            market_trend = "rising"
            demand_velocity = "above_average"
        elif market_score >= 40:
            market_trend = "stable"
            demand_velocity = "steady"
        elif market_score >= 30:
            market_trend = "declining"
            demand_velocity = "below_average"
        else:
            market_trend = "strongly_declining"
            demand_velocity = "low"

        # Generate insights
        insights = self._generate_market_insights(
            market_score,
            {
                "category": category_score,
                "seasonal": seasonal_score,
                "price_position": price_score,
                "demand": demand_score,
                "geographic": geo_score
            },
            notes
        )

        # Generate recommendations
        recommendations = self._generate_market_recommendations(market_score, notes)

        return {
            "agent": self.agent_name,
            "market_score": round(market_score, 1),
            "market_trend": market_trend,
            "demand_velocity": demand_velocity,
            "trend_factors": list(set(trend_factors)),  # Remove duplicates
            "demaybe indicators": list(set(demand_indicators)),
            "insights": insights,
            "notes": "; ".join(notes) if notes else "Market analysis completed",
            "confidence": 0.85,  # Confidence based on internal data quality
            "suggested_actions": recommendations
        }

    def _analyze_category_trends_internal(self, category: str) -> tuple:
        """Analyze trend data for the product category using internal data."""
        score = 0
        notes = []

        # Get trend data from internal sources
        for cat_key, trend_value in self.category_trends.items():
            if cat_key in category or category in cat_key:
                trend_percent = trend_value
                break
        else:
            trend_percent = 0.0  # Default if no match
            notes.append(f"No specific trend data for category '{category}' - using neutral assumption")

        if trend_percent != 0:
            # Convert annual trend to score impact (-10 to +10)
            trend_impact = int(trend_percent / 3)  # Scale down for internal confidence
            score += trend_impact

            if trend_percent > 0:
                notes.append(f"Category '{category}' growing at {trend_percent}% annually (internal data)")
            else:
                notes.append(f"Category '{category}' declining at {abs(trend_percent)}% annually (internal data)")
        else:
            notes.append(f"No significant trend data available for category '{category}'")

        return score, notes

    def _analyze_seasonal_factors_internal(self, category: str, listed_date_str: Optional[str]) -> tuple:
        """Analyze seasonal factors using internal data."""
        score = 0
        notes = []

        if not listed_date_str:
            notes.append("No listing date available for seasonal analysis")
            return score, notes

        try:
            if isinstance(listed_date_str, str):
                listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
            else:
                listed_date = listed_date_str

            current_month = listed_date.month

            # Check seasonal patterns for category
            found_pattern = False
            for cat_key, pattern in self.seasonal_patterns.items():
                if cat_key in category or category in cat_key:
                    if current_month in pattern["peak_months"]:
                        score += 10
                        notes.append(f"Listing during peak season for {cat_key} (month {current_month})")
                    elif current_month in pattern["low_months"]:
                        score -= 10
                        notes.append(f"Listing during low season for {cat_key} (month {current_month})")
                    else:
                        score += 0
                        notes.append(f"Listing during moderate season for {cat_key} (month {current_month})")
                    found_pattern = True
                    break

            if not found_pattern:
                # General seasonal patterns if no specific category match
                # Q4 (Oct-Dec) generally strong for retail
                if current_month in [10, 11, 12]:
                    score += 5
                    notes.append(f"Listing in Q4 (month {current_month}) - typically strong retail period")
                # Q1 (Jan-Mar) often weaker post-holidays
                elif current_month in [1, 2, 3]:
                    score -= 5
                    notes.append(f"Listing in Q1 (month {current_month}) - typically slower post-holiday period")
                else:
                    notes.append(f"Listing in month {current_month} - no strong seasonal bias")

        except Exception as e:
            self._log_debug(f"Date parsing failed for seasonal analysis: {e}")
            notes.append("Could not parse date for seasonal analysis")

        return score, notes

    def _analyze_price_positioning_internal(self, category: str, price: Optional[float], title: str, description: str) -> tuple:
        """Analyze pricing positioning using internal logic."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price specified for market positioning analysis")
            return score, notes

        text_to_analyze = f"{title} {description}"

        # Luxury/premium indicators
        luxury_indicators = ["luxury", "premium", "high-end", "designer", "brand", "authentic", "genuine", "limited edition"]
        luxury_count = sum(1 for indicator in luxury_indicators if indicator in text_to_analyze)

        # Budget/economy indicators
        budget_indicators = ["budget", "cheap", "affordable", "value", "basic", "entry", "used", "second-hand"]
        budget_count = sum(1 for indicator in budget_indicators if indicator in text_to_analyze)

        # Condition indicators
        condition_indicators = ["new", "like new", "excellent", "good", "fair", "poor", "damaged", "broken", "for parts"]
        condition_score = 0
        for condition in condition_indicators:
            if condition in text_to_analyze:
                if condition in ["new", "like new", "excellent"]:
                    condition_score += 2
                elif condition == "good":
                    condition_score += 1
                elif condition == "fair":
                    condition_score += 0
                elif condition in ["poor", "damaged", "broken", "for parts"]:
                    condition_score -= 2
                break

        # Adjust score based on perceived value vs price expectations
        if luxury_count > 0 and condition_score >= 2:
            # Likely premium item - higher prices expected/acceptable
            if price > 500:  # Assuming premium threshold
                score += 5
                notes.append("Price aligns with premium positioning")
            else:
                score -= 5
                notes.append("Price seems low for presumed premium item - verify authenticity")
        elif budget_count > 0:
            # Likely budget item - lower prices expected
            if price < 100:  # Assuming budget threshold
                score += 5
                notes.append("Price aligns with budget positioning")
            else:
                score -= 5
                notes.append("Price seems high for presumed budget item")
        else:
            notes.append("No clear positioning indicators found in description")

        return score, notes

    def _analyze_demand_velocity_internal(self, opportunity_data: dict) -> tuple:
        """Analyze demand velocity using internal indicators."""
        score = 0
        notes = []

        # Check for urgency indicators in title/description
        text_to_check = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()

        urgency_indicators = [
            "must sell", "urgent", "asap", "quick sale", "moving", "leaving",
            "best offer", "price reduced", "reduced", "clearance", "lot", "bulk"
        ]

        urgency_count = sum(1 for indicator in urgency_indicators if indicator in text_to_check)
        if urgency_count > 0:
            score += min(10, urgency_count * 3)  # Up to +10 for urgency
            notes.append(f"Found {urgency_count} urgency indicators suggesting motivated seller")

        # Check for scarcity indicators
        scarcity_indicators = [
            "rare", "limited", "hard to find", "discontinued", "vintage", "antique",
            "collectible", "one of", "only", "few left", "last"
        ]

        scarcity_count = sum(1 for indicator in scarcity_indicators if indicator in text_to_check)
        if scarcity_count > 0:
            score += min(15, scarcity_count * 4)  # Up to +15 for scarcity
            notes.append(f"Found {scarcity_count} scarcity indicators suggesting limited supply")

        # Check listing freshness if we have dates
        listed_date_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        if listed_date_str:
            try:
                if isinstance(listed_date_str, str):
                    listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_date_str

                hours_old = (datetime.now() - listed_date.replace(tzinfo=None)).total_seconds() / 3600

                if hours_old < 6:
                    score += 5
                    notes.append("Very recently listed (<6 hours) - fresh listing")
                elif hours_old < 24:
                    score += 3
                    notes.append("Recently listed (<24 hours)")
                elif hours_old > 168:  # More than a week
                    score -= 5
                    notes.append("Listing older than 1 week - may indicate lower demand")
                elif hours_old > 720:  # More than a month
                    score -= 10
                    notes.append("Listing older than 1 month - potentially stale")

            except Exception as e2:
                self._log_debug(f"Date parsing failed for demand velocity: {e2}")

        return score, notes

    def _analyze_geographic_factors_internal(self, location: str, category: str) -> tuple:
        """Analyze geographic market factors using internal data."""
        score = 0
        notes = []

        # Get real geographic data from internal sources
        if not location:
            notes.append("No location specified for geographic analysis")
            return score, notes

        # Major economic hubs (better markets, more buyers)
        major_markets = [
            "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
            "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
            "fort worth", "columbus", "charlotte", "san francisco", "indianapolis",
            "seattle", "denver", "washington", "boston", "el paso", "nashville",
            "detroit", "oklahoma city", "portland", "las vegas", "memphis", "louisville",
            "baltimore", "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
            "kensington", "london", "manchester", "birmingham", "glasgow", "liverpool",
            "tokyo", "osaka", "shanghai", "beijing", "guangzhou"
        ]

        # Check if location matches major markets
        found_major = False
        for market in major_markets:
            if market in location:
                score += 8
                notes.append(f"Located in major market ({market.title()}) - better buyer pool")
                found_major = True
                break

        if not found_major:
            # Check for remote/rural indicators
            rural_indicators = ["rural", "remote", "countryside", "farm", "ranch", "outback"]
            if any(indicator in location for indicator in rural_indicators):
                score -= 5
                notes.append("Location appears rural/remote - potentially smaller buyer pool")
            else:
                score += 3
                notes.append("Location specified - enables geographic targeting")

        # Shipping cost considerations for heavy/bulky items
        bulk_indicators = ["furniture", "appliance", "equipment", "machinery", "vehicle", "car", "truck", "boat"]
        if any(indicator in category for indicator in bulk_indicators):
            # Coastal cities often better for shipping heavy items
            coastal_cities = ["san francisco", "seattle", "los angeles", "san diego", "new york",
                            "boston", "miami", "houston", "new orleans", "savannah", "charleson"]
            if any(city in location for city in coastal_cities):
                score += 5
                notes.append("Coastal location may reduce shipping costs for bulky items")
            else:
                score -= 3
                notes.append("Inland location may increase shipping costs for bulky items")

        return score, notes

    def _generate_market_insights(self, score: float, factors: dict, notes: list) -> list:
        """Generate insights from the market analysis."""
        insights = []

        # Overall assessment
        if score >= 70:
            insights.append("Strong market conditions - favorable timing for purchase or sale")
        elif score >= 60:
            insights.append("Favorable market conditions with some positive indicators")
        elif score >= 40:
            insights.append("Moderate market conditions - mixed signals present")
        elif score >= 30:
            insights.append("Challenging market conditions - exercise caution")
        else:
            insights.append("Weak market conditions - significant headwinds present")

        # Category-specific insights
        if factors.get("category", 0) > 5:
            insights.append("Operating in a positively trending market category")
        elif factors.get("category", 0) < -5:
            insights.append("Operating in a declining market segment - consider timing")

        # Seasonal insights
        if factors.get("seasonal", 0) > 5:
            insights.append("Well-timed listing taking advantage of seasonal demand")
        elif factors.get("seasonal", 0) < -5:
            insights.append("Off-season listing may affect pricing and time-to-sale")

        # Demand insights
        if factors.get("demand", 0) > 10:
            insights.append("Strong demand indicators suggest motivated seller or scarce item")
        elif factors.get("demand", 0) < -10:
            insights.append("Weak demand indicators suggest caution on pricing expectations")

        return insights[:4]  # Limit to top 4 insights

    def _generate_market_recommendations(self, score: float, notes: list) -> list:
        """Generate actionable recommendations based on market analysis."""
        recommendations = []

        if score >= 70:
            recommendations.append("Consider acting soon - favorable market conditions may not last")
            recommendations.append("Good time to sell if you own similar items")
        elif score >= 60:
            recommendations.append("Monitor market for 1-2 weeks to confirm trend")
            recommendations.append("Standard approach appropriate given current conditions")
        elif score >= 40:
            recommendations.append("Research comparable sales to establish fair value")
            recommendations.append("Consider waiting for better market timing if not urgent")
        elif score >= 30:
            recommendations.append("Exercise patience - market may improve in coming weeks/months")
            recommendations.append("If selling, consider pricing competitively or improving presentation")
        else:
            recommendations.append("Consider postponing non-urgent transactions")
            recommendations.append("If proceeding, conduct thorough due diligence and consider expert appraisal")

        # Specific recommendations based on factors
        if any("season" in note.lower() for note in notes):
            recommendations.append("Consider seasonal timing in your decision-making process")

        if any("major market" in note.lower() for note in notes):
            recommendations.append("Leverage larger buyer pool in metropolitan area")
        elif any("rural" in note.lower() or "remote" in note.lower() for note in notes):
            recommendations.append("Consider wider shipping or local pickup incentives")

        if any("urgency" in note.lower() for note in notes):
            recommendations.append("Motivated seller may provide negotiation leverage")

        return recommendations[:5]  # Limit to top 5 recommendations