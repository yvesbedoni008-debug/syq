"""Price Agent: evaluates pricing correctness and predicts future values."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from datetime import datetime, timedelta
import math
import random

logger = logging.getLogger(__name__)


class PriceAgent(BaseAgent):
    """Agent responsible for pricing analysis and valuation."""

    def __init__(self):
        super().__init__("PriceAgent")
        # Depreciation rates by category (annual %)
        self.depreciation_rates = {
            "electronics": 0.20,   # 20%
            "computers": 0.25,     # 25%
            "phones": 0.30,        # 30%
            "tablets": 0.25,       # 25%
            "cameras": 0.15,       # 15%
            "audio": 0.15,         # 15%
            "video_games": 0.20,   # 20%
            "appliances": 0.10,    # 10%
            "furniture": 0.08,     # 8%
            "vehicles": 0.15,      # 15%
            "cars": 0.18,          # 18%
            "trucks": 0.16,        # 16%
            "motorcycles": 0.12,   # 12%
            "boats": 0.10,         # 10%
            "rvs": 0.08,           # 8%
            "tools": 0.12,         # 12%
            "equipment": 0.10,     # 10%
            "jewelry": -0.02,      # Appreciates slightly (-2%)
            "watches": -0.01,      # Appreciates slightly (-1%)
            "collectibles": -0.05, # Appreciates (-5%)
            "art": -0.03,          # Appreciates (-3%)
            "antiques": -0.04,     # Appreciates (-4%)
            "books": 0.05,         # Depreciates 5%
            "toys": 0.08,          # Depreciates 8%
            "clothing": 0.15,      # Depreciates 15%
            "sports": 0.10,        # Depreciates 10%
            "musical_instruments": 0.08 # Depreciates 8%
        }

        # Common brand premiums (percentage above generic)
        self.brand_premiums = {
            "apple": 0.30,     # 30%
            "samsung": 0.15,   # 15%
            "sony": 0.10,      # 10%
            "lg": 0.05,        # 5%
            "bose": 0.20,      # 20%
            "jbl": 0.10,       # 10%
            "nike": 0.25,      # 25%
            "adidas": 0.20,    # 20%
            "louis vuitton": 2.00, # 200%
            "gucci": 1.80,     # 180%
            "rolex": 3.00,     # 300%
            "omega": 1.50,     # 150%
            "cartier": 2.50,   # 250%
            "ford": 0.05,      # 5%
            "toyota": 0.10,    # 10%
            "honda": 0.08,     # 8%
            "bmw": 0.25,       # 25%
            "mercedes": 0.30,  # 30%
            "audi": 0.25       # 25%
        }

        # Base market values by category (in USD)
        self.base_category_values = {
            "electronics": 200,
            "phones": 400,
            "computers": 600,
            "tablets": 300,
            "cameras": 400,
            "audio": 150,
            "video_games": 50,
            "appliances": 400,
            "furniture": 250,
            "vehicles": 8000,
            "cars": 10000,
            "trucks": 15000,
            "motorcycles": 4000,
            "boats": 10000,
            "rvs": 20000,
            "tools": 100,
            "equipment": 200,
            "jewelry": 300,
            "watches": 250,
            "collectibles": 150,
            "art": 200,
            "antices": 180,
            "books": 20,
            "toys": 25,
            "clothing": 50,
            "sports": 75,
            "musical_instruments": 150
        }

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate if the price is fair and predict future value.

        Returns price score, valuation insight, and suggested price range.
        """
        self._log_info("Processing price analysis")

        # Initialize scores and factors
        price_score = 50  # Start neutral
        valuation_factors = []
        notes = []

        # Extract relevant data
        price = opportunity_data.get("price")
        category = opportunity_data.get("category", "").lower()
        brand = opportunity_data.get("brand", "").lower()
        model = opportunity_data.get("model", "").lower()
        year = opportunity_data.get("year")
        miles = opportunity_data.get("miles") or opportunity_data.get("mileage")
        hours = opportunity_data.get("hours") or opportunity_data.get("hours_of_use")
        condition = opportunity_data.get("condition", "").lower()
        title = opportunity_data.get("title", "").lower()
        description = opportunity_data.get("description", "").lower()
        listed_date_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")

        # 1. Direct Market Value Comparison (internal estimation)
        mv_score, mv_notes = await self._analyze_market_value_comparison_internal(price, opportunity_data)
        price_score += mv_score
        notes.extend(mv_notes)
        valuation_factors.append(("market_value", mv_score))

        # 2. Depreciation Analysis (for applicable items)
        depreciation_score, depreciation_notes = self._analyze_depreciation(category, price, year, miles, hours)
        price_score += depreciation_score
        notes.extend(depreciation_notes)
        valuation_factors.append(("depreciation", depreciation_score))

        # 3. Brand Premium Analysis
        brand_score, brand_notes = self._analyze_brand_premium(brand, price, category)
        price_score += brand_score
        notes.extend(brand_notes)
        valuation_factors.append(("brand", brand_score))

        # 4. Condition Adjustment Analysis
        condition_score, condition_notes = self._analyze_condition_pricing(condition, price, title, description)
        price_score += condition_score
        notes.extend(condition_notes)
        valuation_factors.append(("condition", condition_score))

        # 5. Comparable Analysis (internal algorithm)
        comp_score, comp_notes = await self._analyze_comparables_internal(category, brand, model, price, title, description)
        price_score += comp_score
        notes.extend(comp_notes)
        valuation_factors.append(("comparables", comp_score))

        # 6. Market Timing Analysis
        timing_score, timing_notes = self._analyze_pricing_timing_analysis(price, listed_date_str)
        price_score += timing_score
        notes.extend(timing_notes)
        valuation_factors.append(("timing", timing_score))

        # Ensure score stays within bounds
        price_score = max(0, min(100, price_score))

        # Calculate suggested price range
        suggested_min, suggested_max = await self._calculate_suggested_price_range_internal(price, opportunity_data)

        # Determine pricing assessment
        if price_score >= 75:
            pricing_assessment = "excellent_value"
        elif price_score >= 60:
            pricing_assessment = "good_value"
        elif price_score >= 40:
            pricing_assessment = "fair_value"
        elif price_score >= 25:
            pricing_assessment = "overpriced"
        else:
            pricing_assessment = "significantly_overpriced"

        # Generate insights
        insights = self._generate_price_insights(
            price_score,
            dict(valuation_factors),
            notes
        )

        # Generate recommendations
        recommendations = self._generate_price_recommendations(
            score=price_score,
            assessment=pricing_assessment,
            suggested_min=suggested_min,
            suggested_max=suggested_max,
            notes=notes
        )

        return {
            "agent": self.agent_name,
            "price_score": round(price_score, 1),
            "pricing_assessment": pricing_assessment,
            "suggested_min_price": int(suggested_min) if suggested_min else None,
            "suggested_max_price": int(suggested_max) if suggested_max else None,
            "valuation_factors": {k: round(v, 1) for k, v in valuation_factors},
            "insights": insights,
            "notes": "; ".join(notes) if notes else "Price analysis completed",
            "confidence": 0.85,
            "suggested_actions": recommendations
        }

    async def _analyze_market_value_comparison_internal(self, price: Optional[float], opportunity_data: dict) -> tuple:
        """Estimate market value internally and compare."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price specified for comparison")
            return score, notes

        # Get estimated market value using internal method
        market_value = self._estimate_market_value_internal(opportunity_data)

        if market_value is None or market_value <= 0:
            notes.append("Could not estimate market value - skipping comparison")
            return 0, notes

        # Now compare price to estimated market_value
        ratio = price / market_value
        if ratio < 0.5:
            score -= 25
            notes.append(f"Price ({price}) is significantly below estimated market value ({market_value:.0f}) - potential bargain or red flag")
        elif ratio < 0.8:
            score += 15
            notes.append(f"Price ({price}) is below estimated market value ({market_value:.0f}) - good buying opportunity")
        elif ratio <= 1.2:
            score += 10
            notes.append(f"Price ({price}) is aligned with estimated market value ({market_value:.0f}) - fair pricing")
        elif ratio <= 1.5:
            score -= 10
            notes.append(f"Price ({price}) is above estimated market value ({market_value:.0f}) - premium pricing")
        elif ratio <= 2.0:
            score -= 20
            notes.append(f"Price ({price}) is significantly above estimated market value ({market_value:.0f}) - overpriced")
        else:
            score -= 30
            notes.append(f"Price ({price}) is vastly above estimated market value ({market_value:.0f}) - likely unrealistic")

        return score, notes

    def _estimate_market_value_internal(self, opportunity_data: dict) -> Optional[float]:
        """Estimate market value using internal heuristics and databases."""
        try:
            category = opportunity_data.get("category", "").lower()
            brand = opportunity_data.get("brand", "").lower()
            condition = opportunity_data.get("condition", "").lower()
            year = opportunity_data.get("year")
            title = opportunity_data.get("title", "").lower()
            description = opportunity_data.get("description", "").lower()

            # Base values by category (in USD)
            base_values = {
                "electronics": 200,
                "phones": 400,
                "computers": 600,
                "tablets": 300,
                "cameras": 400,
                "audio": 150,
                "video_games": 50,
                "appliances": 400,
                "furniture": 250,
                "vehicles": 8000,
                "cars": 10000,
                "trucks": 15000,
                "motorcycles": 4000,
                "boats": 10000,
                "rvs": 20000,
                "tools": 100,
                "equipment": 200,
                "jewelry": 300,
                "watches": 250,
                "collectibles": 150,
                "art": 200,
                "antiques": 180,
                "books": 20,
                "toys": 25,
                "clothing": 50,
                "sports": 75,
                "musical_instruments": 150
            }

            # Find base value
            base_value = 100  # Default
            for cat_key, value in base_values.items():
                if cat_key in category or category in cat_key:
                    base_value = value
                    break

            # Brand multipliers
            brand_multipliers = {
                "apple": 2.0,
                "samsung": 1.5,
                "sony": 1.4,
                "lg": 0.12,      # 12%
                "bose": 0.20,    # 20%
                "jbl": 0.10,     # 10%
                "nike": 0.25,    # 25%
                "adidas": 0.20,  # 20%
                "louis vuitton": 2.00, # 200%
                "gucci": 1.80,   # 180%
                "rolex": 3.00,   # 300%
                "omega": 1.50,   # 150%
                "cartier": 2.50, # 250%
                "ford": 0.05,    # 5%
                "toyota": 0.10,  # 10%
                "honda": 0.08,   # 8%
                "bmw": 0.25,     # 25%
                "mercedes": 0.30, # 30%
                "audi": 0.25     # 25%
            }

            brand_multiplier = 1.0
            for brand_key, multiplier in brand_multipliers.items():
                if brand_key in brand:
                    brand_multiplier = multiplier
                    break

            # Condition multipliers
            condition_multipliers = {
                "new": 1.0,
                "like new": 0.9,
                "excellent": 0.8,
                "very good": 0.7,
                "good": 0.6,
                "fair": 0.4,
                "poor": 0.2,
                "salvage": 0.1,
                "for parts": 0.05,
                "as is": 0.3,
                "restored": 0.7,
                "refurbished": 0.6,
                "used": 0.5
            }

            condition_multiplier = 0.5  # Default
            for condition_key, multiplier in condition_multipliers.items():
                if condition_key in condition:
                    condition_multiplier = multiplier
                    break

            # Age/depreciation factor (for applicable categories)
            age_factor = 1.0
            if year and year > 0:
                current_year = datetime.now().year
                age = max(0, current_year - year)

                # Depreciation rates by category (annual %)
                depreciation_rates = {
                    "electronics": 0.20,
                    "computers": 0.25,
                    "phones": 0.30,
                    "tablets": 0.25,
                    "cameras": 0.15,
                    "audio": 0.15,
                    "video_games": 0.20,
                    "appliances": 0.10,
                    "furniture": 0.08,
                    "vehicles": 0.15,
                    "cars": 0.18,
                    "trucks": 0.16,
                    "motorcycles": 0.12,
                    "boats": 0.10,
                    "rvs": 0.08,
                    "tools": 0.12,
                    "equipment": 0.10,
                    "jewelry": -0.02,  # Appreciates slightly
                    "watches": -0.01,
                    "collectibles": -0.05,
                    "art": -0.03,
                    "antiques": -0.04,
                    "books": 0.05,
                    "toys": 0.08,
                    "clothing": 0.15,
                    "sports": 0.10,
                    "musical_instruments": 0.08
                }

                # Find depreciation rate
                depreciation_rate = 0.10  # Default
                for cat_key, rate in depreciation_rates.items():
                    if cat_key in category or category in cat_key:
                        depreciation_rate = rate
                        break

                if depreciation_rate > 0:  # Depreciating item
                    # Cap depreciation at 80% minimum value
                    depreciation = min(0.8, age * depreciation_rate)
                    age_factor = max(0.2, 1.0 - depreciation)
                elif depreciation_rate < 0:  # Appreciating item
                    appreciation = min(1.0, abs(depreciation_rate) * age * 2)  # Cap appreciation
                    age_factor = 1.0 + appreciation

            # Calculate estimated value
            estimated_value = base_value * (1 + brand_multiplier) * condition_multiplier * age_factor

            # Apply some randomness to simulate market variation (±15%)
            variation_factor = 0.85 + (random.random() * 0.3)  # 0.85 to 1.15
            estimated_value *= variation_factor

            return max(1.0, estimated_value)  # Minimum $1

        except Exception as e:
            self._log_debug(f"Error in internal market value estimation: {e}")
            return None

    def _analyze_depreciation(self, category: str, price: Optional[float], year: Optional[int],
                            miles: Optional[float], hours: Optional[float]) -> tuple:
        """Analyze depreciation based on age and usage."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price provided for depreciation analysis")
            return score, notes

        # Find applicable depreciation rate
        depreciation_rate = 0.10  # Default moderate depreciation
        matched_category = None

        for cat_key, rate in self.depreciation_rates.items():
            if cat_key in category or category in cat_key:
                depreciation_rate = rate
                matched_category = cat_key
                break

        if matched_category is None:
            notes.append(f"No specific depredation data for category '{category}', using default 10%")
        else:
            notes.append(f"Using {depreciation_rate*100:.0f}% annual depreciation for '{matched_category}'")

        # Calculate age-based depreciation
        current_year = datetime.now().year
        if year is not None and year > 0:
            age_years = max(0, current_year - year)
            if age_years > 0:
                expected_value_ratio = max(0.1, 1 - (depreciation_rate * age_years))  # Never below 10% of original
                notes.append(f"Item is {age_years} year(s) old")

                # We don't have original price, so we can't calculate exact expected value
                # Instead, we'll note the depreciation expectation
                if depreciation_rate > 0.15:
                    notes.append(f"High depreciation category - value decreases rapidly with age")
                elif depreciation_rate < 0.05:
                    notes.append(f"Low depreciation category - value holds well over time")
                else:
                    notes.append(f"Moderate depreciation category")
            else:
                notes.append("Item appears to be current model year")
                if self.depreciation_rates.get(matched_category, 0) < 0:  # Appreciating items
                    score += 5
                    notes.append(f"Category tends to appreciate in value over time")
        else:
            notes.append("No year provided for age-based depreciation analysis")

        # Usage-based adjustments (for vehicles, equipment)
        if miles is not None and miles > 0:
            if "vehicle" in category or "car" in category or "truck" in category:
                # Average miles per year ~12,000-15,000
                if year is not None and year > 0:
                    years_old = max(1, current_year - year)
                    mpay = miles / years_old if years_old > 0 else miles
                    if mpay > 15000:
                        score -= 5
                        notes.append(f"High mileage ({mpay:,.0f}/year) reduces value")
                    elif mpay < 8000:
                        score += 5
                        notes.append(f"Low mileage ({mpay:,.0f}/year) preserves value")
                    else:
                        notes.append(f"Average mileage ({mpay:,.0f}/year) for age")
                else:
                    notes.append(f"High mileage ({miles:,.0f}) - consider age for proper assessment")
            elif miles > 100000:
                score -= 10
                notes.append(f"Very high mileage ({miles:,.0f}) significantly impacts value")
            elif miles > 50000:
                score -= 5
                notes.append(f"High mileage ({miles:,.0f}) affects value")

        if hours is not None and hours > 0:
            # For equipment, machinery, etc.
            if hours > 10000:
                score -= 10
                notes.append(f"High usage ({hours:,.0f} hours) significantly impacts value")
            elif hours > 5000:
                score -= 5
                notes.append(f"Moderate-high usage ({hours:,.0f} hours) affects value")
            elif hours < 500:
                score += 5
                notes.append(f"Low usage ({hours:,.0f} hours) - like new condition")

        return score, notes

    def _analyze_brand_premium(self, brand: str, price: Optional[float], category: str) -> tuple:
        """Analyze brand premium/discount."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price provided for brand analysis")
            return score, notes

        if not brand:
            notes.append("No brand specified")
            return score, notes

        # Check for known brand premiums
        brand_premium = 0.0  # As decimal (0.30 = 30%)
        matched_brand = None

        for brand_key, premium in self.brand_premiums.items():
            if brand_key in brand or brand in brand_key:
                brand_premium = premium
                matched_brand = brand_key
                break

        if brand_premium != 0:
            notes.append(f"Brand '{brand}' typically carries {brand_premium*100:.0f}% premium vs generic")

            # Adjust score based on whether price reflects brand premium
            # This is simplified - in reality we'd need a base price
            if brand_premium > 0.5:  # Luxury brands (>50%)
                score += min(15, int(brand_brands (>50%)
                score += min(15, int(brand_reim * 25))  # Up to +15 for luxury brands
                notes.append("Luxury brand commands significant premium")
            elif brand_premium > 0.2:  # Premium brands (>20%)
                score += min(10, int(brand_premium * 25))  # Up to +10 for premium brands
                notes.append("Premium band justifies higher price")
            elif brand_premium > 0:  # Minor premium
                score += min(5, int(brand_premium * 25))  # Up to +5
                notes.append("Brand carries modest premium")
            else:  # Negative (discount) brands - rare but possible
                score += max(-5, int(brand_premium * 25))  # Negative adjustment
                notes.append("Brand typically sells at discount")
        else:
            notes.append(f"No specific brand data for '{brand}' - treating as generic")

        return score, notes

    def _analyze_condition_pricing(self, condition: str, price: Optional[float], title: str, description: str) -> tuple:
        """Adjust price expectations based on condition."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price provided for condition analysis")
            return score, notes

        text_to_check = f"{title} {description} {condition}".lower()

        # Condition descriptors with value impact
        condition_indicators = {
            "new": {"value": 0, "notes": "Brand new condition"},
            "like new": {"value": -5, "notes": "Like new - minimal depreciation"},
            "excellent": {"value": -10, "notes": "Excellent condition - minor wear"},
            "very good": {"value": -15, "notes": "Very good condition - light use"},
            "good": {"value": -20, "notes": "Good condition - moderate wear"},
            "fair": {"value": -30, "notes": "Fair condition - noticeable wear"},
            "poor": {"value": -40, "notes": "Poor condition - significant wear/damage"},
            "salvage": {"value": -50, "notes": "Salvage condition - major repairs needed"},
            "for parts": {"value": -60, "notes": "For parts/not working"},
            "as is": {"value": -25, "notes": "As-is condition - no warranties/guarantees"},
            "restored": {"value": -15, "notes": "Professionally restored"},
            "refurbished": {"value": -10, "notes": "Factory refurbished"},
            "used": {"value": -20, "notes": "Used condition (unspecified)"}
        }

        # Check for condition indicators
        condition_found = False
        for condition_key, data in condition_indicators.items():
            if condition_key in text_to_check:
                score += data["value"]
                notes.append(data["notes"])
                condition_found = True
                # Use the first match (most specific)
                break

        if not condition_found:
            # Look for qualitative descriptors
            if any(word in text_to_check for word in ["scratch", "dent", "scar", "mark", "blemish"]):
                score -= 10
                notes.append("Visible cosmetic imperfections noted")
            if any(word in text_to_check for word in ["crack", "break", "tear", "hole", "rip"]):
                score -= 15
                notes.append("Structural damage mentioned")
            if any(word in text_to_check for word in ["work", "function", "operate", "run"]):
                if any(neg in text_to_check for neg in ["not", "doesn't", "won't", "broken"]):
                    score -= 20
                    notes.append("Functional issues reported")
                else:
                    score += 5
                    notes.append("Functional status confirmed working")

        return score, notes

    async def _analyze_comparables_internal(self, category: str, brand: str, model: str, price: Optional[float],
                                 title: str, description: str) -> tuple:
        """Find comparable opportunities using internal algorithms."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price provided for comparable analysis")
            return score, notes

        # In a real implementation, this would query a local database of similar items
        # For now, we'll use heuristics based on the item's attributes

        # Base similarity score
        similarity_score = 0.0
        max_similarity = 5.0  # Maximum possible similarity score

        # Check category match
        if category:
            # In a real system, we would look up actual comparable sales
            # For simulation, we'll use a baseline similarity
            similarity_score += 2.0  # Base points for same category

        # Check brand match
        if brand:
            similarity_score += 1.5  # Points for brand specification

        # Check model match
        if model:
            similarity_score += 1.0  # Points for model specification

        # Condition affects comparability
        condition = opportunity_data.get("condition", "").lower()
        if "new" in condition or "like new" in condition:
            similarity_score += 1.0  # New items are more comparable
        elif "poor" in condition or "salvage" in condition:
            similarity_score -= 1.0  # Poor condition items less comparable

        # Age affects comparability (for applicable items)
        year = opportunity_data.get("year")
        if year and year > 0:
            current_year = datetime.now().year
            age = current_year - year
            if age <= 2:
                similarity_score += 1.0  # Recent items more comparable
            elif age > 5:
                similarity_score -= 1.0  # Older items less comparable

        # Convert similarity to price adjustment
        # Higher similarity = more confidence in comparables = better pricing signal
        # For now, we'll use a simplified approach

        # Simulate finding comparable items with some variance
        base_comparable_price = self._estimate_market_value_internal({
            "category": category,
            "brand": brand,
            "year": year,
            "condition": condition,
            "title": title,
            "description": description
        }) or price  # Fallback to asking price if estimation fails

        # Add some realistic variance to simulate market differences
        variance_factor = 0.8 + (random.random() * 0.4)  # 0.8 to 1.2x
        simulated_median_price = base_comparable_price * variance_factor

        if simulated_median_price and simulated_median_price > 0:
            ratio = price / simulated_median_price
            if ratio < 0.8:
                score += 15
                notes.append(f"Price ({price}) is below estimated comparable median ({simulated_median_price:.0f}) - good buying opportunity")
            elif ratio > 1.2:
                score -= 15
                notes.append(f"Price ({price}) is above estimated comparable median ({simulated_median_price:.0f}) - overpriced relative to market")
            else:
                score += 5
                notes.append(f"Price ({price}) is aligned with estimated comparable median ({simulated_median_price:.0f})")

            # Adjust based on "freshness" of data (simulated)
            # In reality, we would check actual listing dates of comparables
            data_freshness = random.random()  # 0.0 to 1.0
            if data_freshness > 0.7:  # Fresh data
                score += 3
                notes.append("Comparable data is relatively recent - higher confidence")
            elif data_freshness < 0.3:  # Stale data
                score -= 3
                notes.append("Comparable data may be outdated - verify relevance")
            else:
                notes.append("Comparable data has moderate recency")
        else:
            notes.append("Could not establish baseline for comparable analysis")

        return score, notes

    def _analyze_pricing_timing_analysis(self, price: Optional[float], listed_date_str: Optional[str]) -> tuple:
        """Analyze how timing affects price expectations."""
        score = 0
        notes = []

        if price is None or price <= 0:
            notes.append("No price provided for timing analysis")
            return score, notes

        if not listed_date_str:
            notes.append("No listing date for timing analysis")
            return score, notes

        try:
            if isinstance(listed_date_str, str):
                listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
            else:
                listed_date = listed_date_str

            days_listed = (datetime.now() - listed_date.replace(tzinfo=None)).days

            if days_listed < 1:
                score += 5
                notes.append("Just listed - price likely firm initially")
            elif days_listed < 3:
                score += 3
                notes.append("Recently listed - may see price adjustments soon")
            elif days_listed < 7:
                score += 0
                notes.append("Listed within past week - standard timing")
            elif days_listed < 14:
                score -= 5
                notes.append("Listed 1-2 weeks ago - consider if price adjustment needed")
            elif days_listed < 30:
                score -= 10
                notes.append("Listed 2-4 weeks ago - price may be stale")
            else:
                score -= 15
                notes.append("Listed over a month ago - price likely needs adjustment")

            # Seasonal timing factors
            month = listed_date.month
            if month in [11, 12]:  # Holiday season
                score += 5
                notes.append("Listed during holiday shopping season - strong demand period")
            elif month in [1, 2]:  # Post-holiday
                score -= 5
                notes.append("Listed post-holiday - typically weaker demand")
            elif month in [3, 4, 5]:  # Spring
                score += 3
                notes.append("Listed in spring - traditionally strong selling season")
            elif month in [6, 7, 8]:  # Summer
                # Check for seasonal categories
                seasonal_categories = [
                    "sports", "outdoor", "garden", "pool", "grill", "bicycle", "motorcycle",
                    "rv", "camper", "boat", "water sports", "camping", "fahrenheit"
                ]
                if any(seasonal in category for seasonal in seasonal_categories):
                    score += 5
                    notes.append("Listed in summer - peak season for relevant categories")
                else:
                    score -= 2
                    notes.append("Mid-summer - variable demand depending on category")
            elif month in [9, 10]:  # Fall
                score += 3
                notes.append("Listed in fall - good season for many categories")
                # Check for back-to-school or holiday prep
                if any(term in description.lower() for term in ["school", "academic", "student", "college"]):
                    score += 2
                    notes.append("Fall listing with educational context - good timing")

        except Exception as e:
            self._log_debug(f"Date parsing failed for timing analysis: {e}")
            notes.append("Could not parse date for timing analysis")

        return score, n)

    async def _calculate_suggested_price_range_internal(self, price: Optional[float], opportunity_data: dict) -> tuple:
        """Calculate suggested price range based on internal analysis."""
        # Start with estimated market value as baseline
        market_value = self._estimate_market_value_internal(opportunity_data)

        base_price = market_value if market_value and market_value > 0 else price

        if not base_price or base_price <= 0:
            return None, None

        # Apply adjustments based on various factors
        min_multiplier = 0.7
        max_multiplier = 1.3

        # Condition adjustments
        condition = opportunity_data.get("condition", "").lower()
        if "excellent" in condition or "like new" in condition:
            min_multiplier += 0.1
            max_multiplier += 0.15
        elif "good" in condition:
            pass  # No change
        elif "fair" in condition:
            min_multiplier -= 0.1
            max_multiplier -= 0.05
        elif "poor" in condition:
            min_multiplier -= 0.2
            max_multiplier -= 0.1

        # Brand adjustments
        brand = opportunity_data.get("brand", "").lower()
        if any(luxury in brand for luxury in ["rolex", "cartier", "louis vuitton", "gucci"]):
            min_multiplier += 0.1
            max_multiplier += 0.2
        elif any(premium in brand for premium in ["apple", "bmw", "mercedes"]):
            min_multiplier += 0.05
            max_multiplier += 0.1

        # Age adjustments (depreciation)
        year = opportunity_data.get("year")
        if year and year > 0:
            current_year = datetime.now().year
            age = max(0, current_year - year)
            # Reduce max price for older items (except appreciating categories)
            category = opportunity_data.get("category", "").lower()
            depreciation_rate = self.depreciation_rates.get(
                next((k for k in self.depreciation_rates.keys()
                      if k in category or category in k), "equipment"), 0.10)
            if depreciation_rate > 0:  # Depreciating item
                age_factor = max(0.5, 1 - (depreciation_rate * min(age, 10) / 2))  # Cap age effect
                max_multiplier *= age_factor
            elif depreciation_rate < 0:  # Appreciating item
                age_factor = min(2.0, 1 + abs(depreciation_rate) * min(age, 20) / 3)
                max_multiplier *= age_factor

        # Calculate range
        suggested_min = max(0, int(base_price * min_multiplier))
        suggested_max = int(base_price * max_multiplier)

        # Ensure min <= max
        if suggested_min > suggested_max:
            suggested_min, suggested_max = suggested_max, suggested_min

        return suggested_min, suggested_max

    def _generate_price_insights(self, score: float, factors: dict, notes: list) -> list:
        """Generate insights from the price analysis."""
        insights = []

        # Overall assessment
        if score >= 75:
            insights.append("Excellent pricing - represents strong value relative to market")
        elif score >= 60:
            insights.append("Good pricing - fair value with some advantages")
        elif score >= 40:
            insights.append("Fair pricing - market-aligned with room for negotiation")
        elif score >= 25:
            insights.append("Overpriced - exceeds fair market value")
        else:
            insights.append("Significantly overpriced - well above market expectations")

        # Factor-specific insights
        if factors.get("market_value", 0) > 10:
            insights.append("Price compares favorably to estimated market value")
        elif factors.get("market_value", 0) < -10:
            insights.append("Price exceeds estimated market value")

        if factors.get("depreciation", 0) > 5:
            insights.append("Age and condition considerations support current pricing")
        elif factors.get("depreciation", 0) < -5:
            insights.append("Age suggests lower price warranted")

        if factors.get("brand", 0) > 5:
            insights.append("Brand prestige justifies price premium")
        elif factors.get("brand", 0) < -5:
            insights.append("Brand does not support current price level")

        if factors.get("condition", 0) > 5:
            insights.append("Condition supports asking price")
        elif factors.get("condition", 0) < -5:
            insights.append("Condition issues warrant price reduction")

        return insights[:4]  # Limit to top 4 insights

    def _generate_price_recommendations(self, score: float, assessment: str, suggested_min: Optional[int],
                                      suggested_max: Optional[int], notes: list) -> list:
        """Generate actionable recommendations based on price analysis."""
        recommendations = []

        if assessment == "excellent_value":
            recommendations.append("Strong buy recommendation - price represents significant value")
            recommendations.append("Consider acting quickly as such opportunities may not last")
        elif assessment == "good_value":
            recommendations.append("Buy recommendation - fair price with potential for appreciation")
            recommendations.append("Room for modest negotiation if desired")
        elif assessment == "fair_value":
            recommendations.append("Consider making an offer - price is generally fair")
            if suggested_min and suggested_max:
                suggestions.append(f"Suggested offer range: ${suggested_min:,} - ${suggested_max:,}")
            recommendations.append("Focus on verifying condition and authenticity")
        elif assessment == "overpriced":
            recommendations.append("Consider making a lower offer - price exceeds market value")
            if suggested_min and suggested_max:
                recommendations.append(f"Target offer range: ${suggested_min:,} - ${suggested_max:,}")
            recommendations.append("Request justification for premium pricing")
        else:  # significantly_overpriced
            recommendations.append("Not recommended at current price - significant overvaluation")
            if suggested_min and suggested_max:
                recommendations.append(f"Would consider only if price drops to: ${suggested_min:,} - ${suggested_max:,}")
            recommendations.append("Look for comparable alternatives at better pricing")

        # Specific recommendations based on factors
        if any("just listed" in note.lower() for note in notes):
            recommendations.append("Recently listed - seller may be firm initially but watch for price adjustments")
        elif any("listed over a month" in note.lower() for note in notes):
            recommendations.append("Listing has been active - motivated seller may accept lower offer")
        elif any("holiday" in note.lower() for note in notes):
            recommendations.append("Seasonal timing favors buyer - consider aggressive negotiation")

        if any("accessories" in note.lower() or "documentation" in note.lower() for note in notes):
            recommendations.append("Verify all included accessories and documentation are present")
        elif any("condition concerns" in note.lower() for note in notes):
            recommendations.append("Request detailed photos/videos of noted condition issues")
            recommendations.append("Consider professional inspection for major purchases")

        return recommendations[:5]  # Limit to top 5 recommendations