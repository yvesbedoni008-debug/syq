"""Negotiation Agent: develops negotiation strategies and price suggestions based on historical data and market trends."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class NegotiationAgent(BaseAgent):
    """Agent responsible for providing negotiation guidance, price suggestions, and deal structuring."""

    def __init__(self):
        super().__init__("NegotiationAgent")
        # Negotiation leverage factors (positive = buyer advantage, negative = seller advantage)
        self.leverage_factors = {
            "market_conditions": 0.0,      # Will be calculated
            "seller_motivation": 0.0,      # Will be calculated
            "item_condition": 0.0,         # Will be calculated
            "timing": 0.0,                 # Will be calculated
            "alternatives": 0.0,           # Will be calculated
            "information": 0.0             # Will be calculated
        }

        # Strategies based on situation
        self.strategies = {
            "value_based": "Focus on objective market value and condition",
            "problem_solving": "Address seller's motivations and constraints",
            "relationship_building": "Build rapport and trust",
            "anchoring": "Set favorable reference points early",
            "concessions": "Strategic give-and-take on less important items",
            "walk_away": "Maintain ability to terminate negotiation",
            "bundling": "Combine multiple items or services for better deal",
            "silence": "Use pauses strategically to encourage concessions",
            "fogging": "Agree with criticism to reduce defensiveness",
            "negotiation_jujitsu": "Use opponent's energy against them"
        }

        # Common tactics by situation
        self.tactics = {
            "price_anchoring": ["Start with research-based low offer", "Justify with comparable sales"],
            "condition_based": ["Point out wear/defects", "Request expert inspection"],
            "timing_pressure": ["Note listing age", "Mention market softening"],
            "alternative_leveraging": ["Reference similar listings", "Note competing offers"],
            "relationship": ["Find common ground", "Show genuine interest"],
            "bundling": "Ask about accessories, warranties, or related items",
            "information": "Request maintenance records, receipts, documentation",
            "walkaway": "Be prepared to leave if minimum not met",
            "emotional": "Share appropriate personal context (carefully!)",
            "logical": "Present systematic analysis of fair value"
        }

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate negotiation strategy and price guidance.

        Uses opportunity data, market trends, and historical pricing to suggest:
        - Target price range
        - Negotiation tactics
        - Timing advice
        - Deal structure options
        """
        self._log_info("Processing negotiation analysis")

        # Extract relevant data
        price = opportunity_data.get("price", 0)
        market_value = opportunity_data.get("market_value", 0)
        title = opportunity_data.get("title", "").lower()
        description = opportunity_data.get("description", "").lower()
        category = opportunity_data.get("category", "").lower()
        brand = opportunity_data.get("brand", "").lower()
        condition = opportunity_data.get("condition", "").lower()
        seller_info = opportunity_data.get("seller_info", {})
        listed_date_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        photos_count = opportunity_data.get("photos_count", 0)
        video_available = opportunity_data.get("video_available", False)
        location = opportunity_data.get("location", "").lower()
        urgency_indicators = opportunity_data.get("urgency_indicators", [])

        # Analyze negotiation leverage (using enhanced data from other agents)
        leverage_analysis = await self._analyze_negotiation_leverage(
            price, market_value, title, description, category, brand, condition,
            seller_info, listed_date_str, location, urgency_indicators, opportunity_data
        )

        # Determine negotiation stance
        stance, stance_description = self._determine_negotiation_stance(leverage_analysis)

        # Generate target price range
        target_range = self._calculate_target_price_range(
            price, market_value, leverage_analysis, category, brand, condition, opportunity_data
        )

        # Select appropriate strategy
        strategy, strategy_description = self._select_negotiation_strategy(
            leverage_analysis, stance, opportunity_data
        )

        # Choose specific tactics
        tactics = self._select_negotiation_tactics(
            leverage_analysis, strategy, opportunity_data, context
        )

        # Timing advice
        timing_advice = self._generate_timing_advice(
            listed_date_str, leverage_analysis, opportunity_data
        )

        # Deal structure options
        deal_structure = self._suggest_deal_structure(
            opportunity_data, leverage_analysis, target_range
        )

        # Generate insights
        insights = self._generate_negotiation_insights(
            leverage_analysis, stance, target_range, opportunity_data
        )

        # Generate recommendations
        recommendations = self._generate_negotiation_recommendations(
            leverage_analysis, stance, target_range, deal_structure
        )

        # Calculate confidence based on data quality
        confidence = self._calculate_negotiation_confidence(opportunity_data, leverage_analysis)

        # Assess if we're using enhanced data from other agents
        using_real_data = self._check_if_using_real_data(opportunity_data)

        return {
            "agent": self.agent_name,
            "stance": stance,
            "stance_description": stance_description,
            "leverage_score": leverage_analysis["net_leverate"],  # Net buyer advantage (+ve) or disadvantage (-ve)
            "leverage_factors": leverage_analysis["factors"],
            "target_price_range": {
                "min": target_range[0],
                "max": target_range[1],
                "currency": opportunity_data.get("currency", "USD"),
                "target_point": target_range[2]  # Ideal target point
            },
            "recommended_strategy": strategy,
            "strategy_description": strategy_description,
            "tactics": tactics,
            "timing_advice": timing_advice,
            "deal_structure_options": deal_structure,
            "insights": insights,
            "recommendations": recommendations,
            "confidence": round(confidence, 2),
            "data_quality": {
                "using_enhanced_data": using_real_data,
                "confidence_level": "high" if using_real_data else "moderate"
            },
            "preparation_checklist": self._generate_preparation_checklist(opportunity_data, leverage_analysis)
        }

    async def _analyze_negotiation_leverage(self, price: float, market_value: float, title: str, description: str,
                                          category: str, brand: str, condition: str, seller_info: dict,
                                          listed_date_str: str, location: str, urgency_indicators: list,
                                          opportunity_data: dict) -> dict:
        """Analyze negotiation leverage factors using enhanced data."""
        factors = {
            "market_conditions": 0.0,
            "seller_motivation": 0.0,
            "item_condition": 0.0,
            "timing": 0.0,
            "alternatives": 0.0,
            "information": 0.0
        }
        details = {}

        # 1. Market Conditions Leverage - Use real market data from price/trust agents if available
        market_price_ratio = self._get_market_price_ratio(opportunity_data)
        if market_price_ratio is not None:
            if market_price_ratio > 1.2:  # Overpriced
                factors["market_conditions"] += 15  # Buyer advantage
                details["market_conditions"] = f"Asking price {((market_price_ratio-1)*100):.0f}% above market value"
            elif market_price_ratio < 0.8:  # Underpriced
                factors["market_conditions"] -= 10  # Seller advantage (or potential scam)
                details["market_conditions"] = f"Asking price {((1-market_price_ratio)*100):.0f}% below market value"
            else:
                factors["market_conditions"] += 0  # Neutral
                details["market_conditions"] = "Price aligned with market value"
        else:
            # Fallback to original logic if no market data available
            if market_value > 0 and price > 0:
                price_to_market_ratio = price / market_value
                if price_to_market_ratio > 1.2:  # Overpriced
                    factors["market_conditions"] += 15  # Buyer advantage
                    details["market_conditions"] = f"Asking price {((price_to_market_ratio-1)*100):.0f}% above market"
                elif price_to_market_ratio < 0.8:  # Underpriced
                    factors["market_conditions"] -= 10  # Seller advantage (or potential scam)
                    details["market_conditions"] = f"Asking price {((1-price_to_market_ratio)*100):.0f}% below market"
                else:
                    factors["market_conditions"] += 0  # Neutral
                    details["market_conditions"] = "Price aligned with market value"
            else:
                factors["market_conditions"] = 0
                details["market_conditions"] = "Insufficient data for market comparison"

        # 2. Seller Motivation
        motivation_score = 0
        motivation_details = []

        # Check listing age
        if listed_date_str:
            try:
                if isinstance(listed_date_str, str):
                    listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_date_str
                days_listed = (datetime.now() - listed_date.replace(tzinfo=None)).days

                if days_listed > 30:
                    motivation_score += 15
                    motivation_details.append(f"Listed {days_listed} days ago - potentially motivated seller")
                elif days_listed > 14:
                    motivation_score += 8
                    motivation_details.append(f"Listed {days_listed} days ago - some motivation possible")
                elif days_listed < 2:
                    motivation_score -= 5
                    motivation_details.append("Just listed - seller likely firm on price")
            except:
                pass

        # Check for explicit urgency indicators
        urgency_text = " ".join(urgency_indicators) if isinstance(urgency_indicators, list) else str(urgency_indicators)
        urgency_text = f"{title} {description} {urgency_text}".lower()

        urgency_phrases = [
            "must sell", "need to sell", "moving", "relocating", "deployed",
            "divorce", "financial hardship", "medical bills", "estate sale",
            "price reduced", "reduced", "best offer", "make offer"
        ]

        urgency_matches = sum(1 for phrase in urgency_phrases if phrase in urgency_text)
        if urgency_matches >= 2:
            motivation_score += 12
            motivation_details.append("Multiple urgency indicators suggest motivated seller")
        elif urgency_matches == 1:
            motivation_score += 6
            motivation_details.append("Some urgency indicators present")

        # Check for seller motivation from profile
        if seller_info.get("reason_for_sale"):
            reason = seller_info["reason_for_sale"].lower()
            if any(word in reason for word in ["moving", "relocating", "deployed", "upgrade"]):
                motivation_score += 10
                motivation_details.append("Seller reason suggests motivation")
            elif any(word in reason for word in ["financial", "debt", "bill"]):
                motivation_score += 15
                motivation_details.append("Financial motivation indicated - strong leverage")

        factors["seller_motivation"] = max(-20, min(20, motivation_score))  # Cap at +/-20
        details["seller_motivation"] = "; ".join(motivation_details) if motivation_details else "No clear motivation signals"

        # 3. Item Condition
        condition_score = 0
        condition_details = []

        # Negative condition factors help buyer
        if any(word in condition for word in ["fair", "poor", "damaged", "broken", "needs repair"]):
            condition_score -= 10
            condition_details.append("Room for negotiation based on condition")
        elif any(word in condition for word in ["excellent", "like new", "new"]):
            condition_score += 5
            condition_details.append("Excellent condition limits negotiation room")

        # Check description for condition issues
        issue_indicators = ["scratch", "dent", "wear", "tear", "stain", "fade", "rust", "corrosion"]
        issue_count = sum(1 for indicator in issue_indicators if indicator in description)
        if issue_count >= 3:
            condition_score -= 8
            condition_details.append("Multiple cosmetic issues noted")
        elif issue_count >= 1:
            condition_score -= 4
            condition_details.append("Some cosmetic wear indicated")

        # Check for functionality issues
        if any(word in description for word in ["not working", "broken", "defective", "faulty"]):
            condition_score -= 15
            condition_details.append("Functional issues present - significant negotiation room")
        elif any(word in description for word in ["occasionally", "sometimes", "intermittent"]):
            if any(word in description for word in ["works", "functional", "operational"]):
                condition_score -= 6
                condition_details.append("Intermittent issues noted")

        factors["item_condition"] = max(-15, min(15, condition_score))  # Cap at +/-15
        details["item_condition"] = "; ".join(condition_details) if condition_details else "Condition appears good"

        # 4. Timing Factors
        timing_score = 0
        timing_details = []

        # Get enhanced timing data from market agent if available
        timing_enhancement = self._get_timing_enhancement(opportunity_data)
        if timing_enhancement:
            timing_score += timing_enhancement.get("score_adjustment", 0)
            timing_details.append(f"Market timing analysis: {timing_enhancement.get('assessment', 'N/A')}")

        # Seasonal timing
        month = datetime.now().month
        seasonal_factors = {
            "q4": [11, 12, 1],      # Holiday season - seller advantage for gifts
            "q1": [2, 3, 4],        # Post-holiday - buyer advantage
            "q2": [5, 6, 7],        # Spring/summer - mixed
            "q3": [8, 9, 10]        # Fall - seller advantage for school/holidays prep
        }

        if "electronics" in category or "gaming" in category or "phone" in category:
            if month in seasonal_factors["q1"]:  # Jan-Mar post-holiday
                timing_score += 10
                timing_details.append("Post-holiday period - good time to buy electronics")
            elif month in seasonal_factors["q4"]:  # Oct-Dec holiday
                timing_score -= 8
                timing_details.append("Holidier season - higher demand for electronics")

        elif "vehicle" in category or "car" in category:
            if month in [1, 2]:  # Winter - slower market
                timing_score += 8
                timing_details.append("Winter months - typically slower auto market")
            elif month in [7, 8]:  # Summer peak
                timing_score -= 5
                timing_details.append("Summer peak season - stronger seller position")

        elif "sports" in category or "outdoor" in category:
            if month in [11, 12, 1, 2]:  # Winter
                timing_score -= 5
                timing_details.append("Off-season for outdoor gear - limited demand")
            elif month in [5, 6, 7, 8]:  # Summer
                timing_score += 8
                timing_details.append("Peak season for outdoor - better selling period")

        # Listing timing patterns
        if listed_date_str:
            try:
                if isinstance(listed_date_str, str):
                    listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_date_str
                hour_listed = listed_date.hour
                # Listings during work hours may get less immediate attention
                if 9 <= hour_listed <= 17:
                    timing_score += 2
                    timing_details.append("Listed during business hours - may get less weekend attention")
            except:
                pass

        factors["timing"] = max(-15, min(15, timing_score))  # Cap at +/-15
        details["timing"] = "; ".join(timing_details) if timing_details else "Standard timing considerations"

        # 5. Alternatives (Competing Options)
        alternatives_score = 0
        alternatives_details = []

        # Get enhanced alternatives data from market agent if available
        alternatives_enhancement = self._get_alternatives_enhancement(opportunity_data)
        if alternatives_enhancement:
            alternatives_score += alternatives_enhancement.get("score_adjustment", 0)
            alternatives_details.append(f"Market alternatives analysis: {alternatives_enhancement.get('assessment', 'N/A')}")

        # This would ideally come from market data - simplified heuristic
        if photos_count == 0:
            alternatives_score -= 5
            alternatives_details.append("No photos makes comparison difficult - may indicate fewer genuine buyers")
        elif photos_count >= 10:
            alternatives_score += 5
            alternatives_details.append("High-quality listing with many photos may attract more competition")

        # Check if item seems specialized/common
        common_indicators = ["generic", "basic", "standard", "universal"]
        rare_indicators = ["rare", "limited", "unique", "vintage", "antique", "collectible", "one of"]

        common_count = sum(1 for indicator in common_indicators if indicator in description)
        rare_count = sum(1 for indicator in rare_indicators if indicator in description)

        if rare_count > 0:
            alternatives_score -= 8
            alternatives_details.append("Appears to be rare/uncommon item - fewer alternatives")
        elif common_count > 0:
            alternatives_score += 6
            alternatives_details.append("Common item - many alternatives likely available")

        factors["alternatives"] = max(-15, min(15, alternatives_score))
        details["alternatives"] = "; ".join(alternatives_details) if alternatives_details else "Standard market competition"

        # 6. Information Asymmetry
        info_score = 0
        info_details = []

        # Get enhanced information data from trust/risk agents if available
        info_enhancement = self._get_information_enhancement(opportunity_data)
        if info_enhancement:
            info_score += info_enhancement.get("score_adjustment", 0)
            info_details.append(f"Information symmetry analysis: {info_enhancement.get('assessment', 'N/A')}")

        # Who has more information?
        if video_available:
            info_score += 5
            info_details.append("Video available - good for buyer assessment")
        elif photos_count >= 5:
            info_score += 3
            info_details.append("Multiple photos available - decent visual information")

        # Documentation
        doc_indicators = ["manual", "paperwork", "documentation", "receipt", "warranty", "service records"]
        doc_count = sum(1 for indicator in doc_indicators if indicator in description)
        if doc_count >= 2:
            info_score -= 4
            info_details.append("Good documentation available - reduces buyer uncertainty")
        elif doc_count == 0:
            info_score += 6
            info_details.append("No documentation mentioned - increases buyer risk")

        # History/background
        history_indicators = ["history", "background", "provenance", "origin", "previous owner"]
        history_count = sum(1 for indicator in history_indicators if indicator in description)
        if history_count >= 2:
            info_score -= 3
            info_details.append("Good history/provenance information available")
        elif history_count == 0 and ("antique" in description or "vintage" in description):
            info_score += 8
            info_details.append("Vintage/antique item with unknown history - higher risk")

        # Specifications detail
        spec_indicators = ["specification", "specs", "dimensions", "weight", "capacity", "runtime", "resolution"]
        spec_count = sum(1 for indicator in spec_indicators if indicator in description)
        if spec_count >= 3:
            info_score -= 4
            info_details.append("Detailed specifications available")
        elif spec_count == 0 and any(word in description for word in ["electronic", "mechanical", "technical"]):
            info_score += 5
            info_details.append("Technical item lacking specifications - harder to evaluate")

        factors["information"] = max(-15, min(15, info_score))
        details["information"] = "; ".join(info_details) if info_details else "Standard information availability"

        # Calculate net leverage (positive = buyer advantage, negative = seller advantage)
        net_leverate = sum(factors.values())

        return {
            "factors": factors,
            "details": details,
            "net_leverate": net_leverate
        }

    def _get_market_price_ratio(self, opportunity_data: dict) -> Optional[float]:
        """Get market price ratio from price agent analysis if available."""
        price_analysis = opportunity_data.get("price", {})
        if isinstance(price_analysis, dict):
            # Check if we have market value comparison data
            market_value = price_analysis.get("market_value_used")
            price = opportunity_data.get("price")
            if market_value and market_value > 0 and price and price > 0:
                return price / market_value
            # Alternatively, check valuation factors
            valuation_factors = price_analysis.get("valuation_factors", {})
            if "market_value" in valuation_factors:
                market_score = valuation_factors["market_value"]
                # Convert score back to approximate ratio (this is approximate)
                # Score of +15 means good buying opportunity (price < market)
                # Score of -15 means overpriced (price > market)
                if market_score != 0:
                    # Rough conversion: score/15 * 0.2 = percentage deviation from 1.0
                    # So score of +15 = 20% below market (ratio = 0.8)
                    # Score of -15 = 20% above market (ratio = 1.2)
                    deviation = (market_score / 15) * 0.2
                    return 1.0 - deviation  # Convert to price/market ratio
        return None

    def _get_timing_enhancement(self, opportunity_data: dict) -> Optional[dict]:
        """Get timing enhancement from market agent analysis."""
        market_analysis = opportunity_data.get("market", {})
        if isinstance(market_analysis, dict):
            # Look for timing-related insights
            insights = market_analysis.get("insights", [])
            for insight in insights:
                if "timing" in insight.lower() or "season" in insight.lower():
                    # Return a structured enhancement
                    return {
                        "score_adjustment": 5 if "favorable" in insight.lower() or "good" in insight.lower() else -5 if "unfavorable" in insight.lower() or "poor" in insight.lower() else 0,
                        "assessment": insight
                    }
        return None

    def _get_alternatives_enhancement(self, opportunity_data: dict) -> Optional[dict]:
        """Get alternatives enhancement from market agent analysis."""
        market_analysis = opportunity_data.get("market", {})
        if isinstance(market_analysis, dict):
            # Look for competition/alternatives related insights
            insights = market_analysis.get("insights", [])
            for insight in insights:
                if any(word in insight.lower() for word in ["competition", "alternative", "market", "demand"]):
                    # Return a structured enhancement
                    if "strong" in insight.lower() or "high" in insight.lower():
                        return {"score_adjustment": -5, "assessment": insight}  # High competition = seller advantage
                    elif "low" in insight.lower() or "limited" in insight.lower():
                        return {"score_adjustment": 5, "assessment": insight}  # Low competition = buyer advantage
                    else:
                        return {"score_adjustment": 0, "assessment": insight}
        return None

    def _get_information_enhancement(self, opportunity_data: dict) -> Optional[dict]:
        """Get information enhancement from trust/risk agent analysis."""
        # Check trust agent for verification info
        trust_analysis = opportunity_data.get("trust", {})
        if isinstance(trust_analysis, dict):
            insights = trust_analysis.get("insights", [])
            for insight in insights:
                if any(word in insight.lower() for word in ["documentation", "verification", "authentic", "certificate"]):
                    if "verified" in insight.lower() or "authentic" in insight.lower():
                        return {"score_adjustment": -5, "assessment": insight}  # Good verification = less info asymmetry
                    elif "unverified" in insight.lower() or "missing" in insight.lower():
                        return {"score_adjustment": 5, "assessment": insight}  # Poor verification = more info asymmetry

        # Check risk agent for documentation risks
        risk_analysis = opportunity_data.get("risk", {})
        if isinstance(risk_analysis, dict):
            risk_details = risk_analysis.get("risk_details", [])
            for detail in risk_details:
                if "documentation" in detail.lower():
                    if "no documentation" in detail.lower() or "missing" in detail.lower():
                        return {"score_adjustment": 5, "assessment": detail}  # Missing docs = more info asymmetry
                    elif "good documentation" in detail.lower():
                        return {"score_adjustment": -5, "assessment": detail}  # Good docs = less info asymmetry
        return None

    def _check_if_using_real_data(self, opportunity_data: dict) -> bool:
        """Check if the opportunity data indicates we're using enhanced data from other agents."""
        # Check multiple agents for confidence indicators
        agents_to_check = ["price", "trust", "risk", "market"]
        high_confidence_count = 0
        total_checked = 0

        for agent_key in agents_to_check:
            analysis = opportunity_data.get(agent_key, {})
            if isinstance(analysis, dict):
                confidence = analysis.get("confidence", 0.5)
                if confidence > 0.75:  # High confidence threshold
                    high_confidence_count += 1
                total_checked += 1

        # If majority of checked agents have high confidence, we're likely using real data
        return total_checked > 0 and (high_confidence_count / total_checked) >= 0.5

    # Keep all the remaining methods the same as they don't need direct external access
    # (_determine_negotiation_stance, _select_negotiation_strategy, etc.)

    def _determine_negotiation_stance(self, leverage_analysis: dict) -> tuple:
        """Determine whether to take aggressive, moderate, or conservative stance."""
        net_leverate = leverage_analysis["net_leverate"]
        factors = leverage_analysis["factors"]

        if net_leverate >= 15:
            return "strong_buyer_favorable", "Strong buyer advantage - can be aggressive in negotiations"
        elif net_leverate >= 5:
            return "moderately_buyer_favorable", "Moderate buyer advantage - firm but reasonable approach"
        elif net_leverate <= -15:
            return "strong_seller_favorable", "Strong seller advantage - may need to accept terms or walk away"
        elif net_leverate <= -5:
            return "moderately_seller_favorable", "Moderator seller advantage - competitive but respectful approach"
        else:
            return "neutral", "Relatively balanced position - focus on mutual benefit and fairness"

    def _select_negotiation_strategy(self, leverage_analysis: dict, stance: str,
                                   opportunity_data: dict) -> tuple:
        """Select the most appropriate negotiation strategy."""
        # Strategy selection based on context
        category = opportunity_data.get("category", "").lower()
        condition = opportunity_data.get("condition", "").lower()
        seller_info = opportunity_data.get("seller_info", {})
        price = opportunity_data.get("price", 0)
        market_value = opportunity_data.get("market_value", 0)

        # High-value items need different approach
        if price > 5000:
            return "relationship_building", self.strategies["relationship_building"]

        # Safety/legal concerns
        if any(word in opportunity_data.get("description", "").lower()
               for word in ["title", "lien", "loan", "finance"]):
            return "problem_solving", self.strategies["problem_solving"]

        # High motivation scenarios
        if abs(leverage_analysis["factors"]["seller_motivation"]) >= 10:
            if leverage_analysis["factors"]["seller_motivation"] > 0:  # Seller motivated
                return "problem_solving", self.strategies["problem_solving"]
            else:  # Buyer motivated (rare but possible)
                return "value_based", self.strategies["value_based"]

        # Condition-based negotiations
        if any(word in condition for word in ["fair", "poor", "damaged", "needs repair"]):
            return "problem_solving", self.strategies["problem_solving"]

        # Market advantages
        if leverage_analysis["factors"]["market_conditions"] >= 10:
            return "value_based", self.strategies["value_based"]

        # Information advantage
        if abs(leverage_analysis["factors"]["information"]) >= 10:
            if leverage_analysis["factors"]["information"] > 0:  # Buyer has info advantage
                return "value_based", self.strategies["value_based"]
            else:  # Seller has info advantage
                return "relationship_building", self.strategies["relationship_building"]

        # Default to value-based for most situations
        return "value_based", self.strategies["value_based"]

    def _select_negotiation_tactics(self, leverage_analysis: dict, strategy: str,
                                  opportunity_data: dict, context: Optional[Dict[str, Any]]) -> List[str]:
        """Select specific tactics based on strategy and situation."""
        tactics = []
        category = opportunity_data.get("category", "").lower()
        condition = opportunity_data.get("condition", "").lower()
        price = opportunity_data.get("price", 0)

        # Always include some universal good tactics
        tactics.append("Research comparable sales thoroughly beforehand")
        tactics.append("Set your walkaway point before starting negotiation")

        # Strategy-specific tactics
        if strategy == "value_based":
            tactics.extend(self.tactics["price_anchoring"])
            if market_value > 0:
                tactics.append(f"Reference market value of ${market_value:,.0f} in discussions")
            if opportunity_data.get("photos_count", 0) < 3:
                tactics.append("Request additional photos to verify condition claims")

        elif strategy == "problem_solving":
            tactics.extend(self.tactics["condition_based"])
            if "water" in opportunity_data.get("description", "").lower():
                tactics.append("Ask specifically about water damage or moisture exposure")
            if "electronic" in category:
                tactics.append("Request to power on and test functionality")
            if "vehicle" in category:
                tactics.append("Ask for maintenance records and service history")
                # Note: Fixed typo from original - was "tatics" now "tactics"
                tactics.append("Consider requesting pre-purchase inspection")

        elif strategy == "relationship_building":
            tactics.extend(self.tactics["relationship"])
            # Find something genuine to compliment
            if any(word in opportunity_data.get("title", "").lower()
                   for word in ["classic", "vintage", "rare", "unique"]):
                tactics.append("Acknowledge the item's unique qualities or history")
            elif any(word in opportunity_data.get("description", "").lower()
                     for word in ["well maintained", "cared for", "loved"]):
                tactics.append("Recognize the care that's gone into maintaining the item")

        elif strategy == "anchoring":
            # Start far from target but reasonable
            target_low, target_high, target_mid = self._calculate_target_price_range(
                opportunity_data.get("price", 0),
                opportunity_data.get("market_value", 0),
                {"factors": {"market_conditions": 0}},  # Simplified
                opportunity_data.get("category", ""),
                opportunity_data.get("brand", ""),
                opportunity_data.get("condition", "")
            )
            anchor_price = max(1, int(target_low * 0.7))  # Start 30% below target low
            tactics.append(f"Consider opening with offer of ${anchor_price:,.0f} to anchor low")
            tactics.append("Have ready justifications based on comparable sales")

        elif strategy == "bundling":
            tactics.extend(self.tactics["bundling"])
            # Suggest specific bundles based on category
            if "electronic" in category:
                tactics.append("Ask about charging cables, cases, or extra batteries")
            elif "camera" in category:
                tactics.append("Inquire about lenses, flashes, or memory cards")
            elif "vehicle" in category:
                tactics.append("Ask about spare keys, maintenance records, or recent tires")
            elif "furniture" in category:
                tactics.append("See if they have matching pieces or decorative accessories")

        elif strategy == "information":
            tactics.extend(self.tactics["information"])
            # Be specific about what to request
            if "service" in opportunity_data.get("description", "").lower():
                tactics.append("Request complete service history and records")
            if any(word in opportunity_data.get("title", "").lower() for word in ["watch", "jewelry"]):
                tactics.append("Ask for original papers, box, and authenticity certificates")
            if "vehicle" in category:
                tactics.append("Request CARFAX or equivalent vehicle history report")

        # Add context-specific tactical advice
        if opportunity_data.get("seller_info", {}).get("feedback_count", 0) < 10:
            tactics.append("Exercise extra caution with low-feedback sellers - consider smaller initial transaction")

        if any(word in opportunity_data.get("description", "").lower()
               for word in ["as is", "where is", "no returns"]):
            tactics.append("'As-is' sale requires extra diligence - consider professional inspection")

        # Limit and deduplicate
        seen = set()
        unique_tactics = []
        for tactic in tactics:
            if tactic not in seen:
                seen.add(tactic)
                unique_tactics.append(tactic)

        return unique_tactics[:8]  # Return top 8 tactics

    def _calculate_target_price_range(self, price: float, market_value: float,
                                    leverage_analysis: dict, category: str,
                                    brand: str, condition: str, opportunity_data: dict) -> tuple:
        """Calculate target price range for negotiation."""
        # Start with market value or asking price as baseline
        # Prefer market value from enhanced data if available
        base_price = None

        # Try to get enhanced market value
        enhanced_market_value = self._get_enhanced_market_value(opportunity_data)
        if enhanced_market_value is not None and enhanced_market_value > 0:
            base_price = enhanced_market_value
        elif market_value > 0:
            base_price = market_value
        elif price > 0:
            base_price = price
        else:
            return (0, 0, 0)  # No basis for calculation

        # Apply adjustments
        min_pct = 0.80   # Start willing to pay 80% of base
        max_pct = 1.10   # Willing to go up to 110% of base (for exceptional items)
        target_pct = 0.90  # Ideal target

        # Adjust based on leverage
        net_leverate = leverage_analysis["net_leverate"]
        # Positive leverage = buyer advantage = can go lower
        # Negative leverage = seller advantage = need to pay more
        adjustment_factor = - (net_leverate * 0.003)  # Scale factor

        min_pct += adjustment_factor
        max_pct += adjustment_factor
        target_pct += adjustment_factor

        # Apply bounds
        min_pct = max(0.50, min(0.95, min_pct))   # Between 50-95%
        max_pct = max(0.90, min(1.50, max_pct))   # Between 90-150%
        target_pct = max(0.60, min(1.20, target_pct))  # Between 60-120%

        # Category-specific adjustments
        category_lower = (category or "").lower()
        if any(luxury in category_lower for luxury in ["jewelry", "watch", "luxury", "designer"]):
            # Luxury items often hold value better, less room to bargain down
            min_pct *= 0.9  # Reduce minimum slightly
            max_pct *= 1.05  # Increase maximum slightly
        elif any(tech in category_lower for tech in ["electronic", "computer", "phone"]):
            # Tech depreciates fast - more room to negotiate down
            min_pct *= 0.85  # Can go lower
            max_pct *= 0.95  # Less willing to pay premium
        elif any(vehicle in category_lower for vehicle in ["car", "truck", "vehicle"]):
            # Cars have established markets - stick closer to book value
            adjustment = 0.02  # Small adjustment toward market
            min_pct = min_pct * (1 - adjustment) + 0.88 * adjustment
            max_pct = max_pct * (1 - adjustment) + 1.12 * adjustment
            target_pct = target_pct * (1 - adjustment) + 1.00 * adjustment

        # Condition adjustments
        condition_lower = (condition or "").lower()
        if any(word in condition_lower for word in ["excellent", "like new", "new"]):
            # Excellent condition - less room to go down
            min_pct *= 1.05
            max_pct *= 1.05
        elif any(word in condition_lower for word in ["fair", "poor", "damaged", "broken"]):
            # Poor condition - can go much lower
            min_pct *= 0.8
            max_pct *= 0.9

        # Calculate final values
        min_price = max(0, int(base_price * min_pct))
        max_price = int(base_price * max_pct)
        target_price = int(base_price * target_pct)

        # Ensure min <= target <= max
        if min_price > target_price:
            min_price, target_price = target_price, min_price
        if max_price < target_price:
            max_price = target_price
        if min_price > max_price:
            min_price = max_price

        return (min_price, max_price, target_price)

    def _get_enhanced_market_value(self, opportunity_data: dict) -> Optional[float]:
        """Get enhanced market value from price agent analysis."""
        price_analysis = opportunity_data.get("price", {})
        if isinstance(price_analysis, dict):
            # Check if we have a direct market value from analysis
            market_value = price_analysis.get("market_value_used")
            if market_value and isinstance(market_value, (int, float)) and market_value > 0:
                return float(market_value)

            # Check suggested price range
            suggested_range = price_analysis.get("suggested_price_range", {})
            if isinstance(suggested_range, dict):
                min_price = suggested_range.get("min")
                max_price = suggested_range.get("max")
                if min_price and max_price:
                    return (float(min_price) + float(max_price)) / 2

            # Check valuation factors for market value component
            valuation_factors = price_analysis.get("valuation_factors", {})
            if isinstance(valuation_factors, dict) and "market_value" in valuation_factors:
                # This is a score, not actual value, but we can use it relatively
                market_score = valuation_factors["market_value"]
                # Convert score to approximate multiplier
                # Score +15 = 20% below market -> multiplier 1.2
                # Score -15 = 20% above market -> multiplier 0.8
                # Score 0 = at market -> multiplier 1.0
                price = opportunity_data.get("price", 0)
                if price > 0 and market_score != 0:
                    # Rough conversion: each point = ~1.33% adjustment
                    adjustment = (market_score * 0.0133)
                    estimated_market_value = price / (1 + adjustment) if adjustment != -1 else price * 2
                    return max(0, estimated_market_value)
        return None

    def _generate_timing_advice(self, listed_date_str: str, leverage_analysis: dict,
                              opportunity_data: dict) -> str:
        """Generate timing-specific negotiation advice."""
        advice_parts = []

        if not listed_date_str:
            return "No timing information available - proceed when ready"

        try:
            if isinstance(listed_date_str, str):
                listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
            else:
                listed_date = listed_date_str

            days_listed = (datetime.now() - listed_date.replace(tzinfo=None)).days
            hour_listed = listed_date.hour if hasattr(listed_date, 'hour') else 12

            # Timing based on listing age
            if days_listed == 0:
                advice_parts.append("Just listed today - seller likely firm initially")
                advice_parts.append("Consider waiting 2-3 days for potential price adjustment")
            elif days_listed <= 2:
                advice_parts.append("Listed very recently - may need to make strong offer to stand out")
            elif days_listed <= 7:
                advice_parts.append("Listed within past week - standard negotiation timing")
            elif days_listed <= 14:
                advice_parts.append("Listed 1-2 weeks ago - good time to make reasonable offer")
            elif days_listed <= 30:
                advice_parts.append("Listed 2-4 weeks ago - motivated seller possible")
                advice_parts.append("Consider making fair offer based on market value")
            else:
                advice_parts.append("Listed over a month ago - likely motivated to sell")
                advice_parts.append("Can make lower offer but be prepared for counter")

            # Time of day/week considerations
            if 9 <= hour_listed <= 17:  # Business hours
                advice_parts.append("Listed during business hours - consider timing offer for evening/weekend")
            elif 18 <= hour_listed <= 21:  # Evening
                advice_parts.append("Listed in evening - good timing for prompt response")

            # Day of week
            weekday = listed_date.weekday()  # 0=Monday, 6=Sunday
            if weekday >= 5:  # Weekend
                advice_parts.append("Weekend listing - may get more attention but also more competition")
            else:  # Weekday
                advice_parts.append("Weekday listing - potentially less competition initially")

            # Market timing advice
            market_trend = "unknown"  # Would come from market agent in full implementation
            if "market" in opportunity_data:
                market_data = opportunity_data["market"]
                if isinstance(market_data, dict):
                    market_trend = market_data.get("market_trend", "unknown")

            if market_trend == "declining" and days_listed > 7:
                advice_parts.append("In declining market, consider acting sooner rather than later")
            elif market_trend == "rising" and days_listed > 14:
                advice_parts.append("In rising market with aged listing - possible opportunity")

        except Exception as e:
            self._log_debug(f"Error in timing advice calculation: {e}")
            advice_parts.append("Unable to parse listing date for specific timing advice")

        return " ".join(advice_parts) if advice_parts else "Standard timing applies - be prepared and patient"

    def _suggest_deal_structure(self, opportunity_data: dict, leverage_analysis: dict,
                              target_range: tuple) -> List[Dict[str, Any]]:
        """Suggest different deal structures for the negotiation."""
        structures = []
        min_price, max_price, target_price = target_range

        # Standard purchase
        structures.append({
            "type": "straight_purchase",
            "description": "Pay agreed amount and take possession",
            "buyer_protection": "Standard - verify before payment",
            "typical_use": "Most transactions",
            "price_range": {"min": min_price, "max": max_price, "target": target_price}
        })

        # Escrow option (for higher value)
        if target_price > 200:
            structures.append({
                "type": "escrow_service",
                "description": "Use trusted third party to hold funds until both parties satisfied",
                "buyer_protection": "High - funds released only after verification",
                "typical_use": "Transactions over $200, or when trust is uncertain",
                "price_range": {"min": min_price, "max": max_price, "target": target_price}
            })

        # Deposit + balance
        if target_price > 100:
            deposit_amount = min(50, int(target_price * 0.1))  # 10% or $50 max
            structures.append({
                "type": "deposit_balance",
                "description": f"Pay ${deposit_amount} deposit, balance upon verification",
                "buyer_protection": "Medium - limits initial risk",
                "typical_use": "Local pickup or when concerned about item as described",
                "price_range": {
                    "min": max(0, min_price - deposit_amount),
                    "max": max_price - deposit_amount,
                    "target": target_price - deposit_amount
                }
            })

        # Trade or partial trade
        if "trade" in opportunity_data.get("description", "").lower():
            structures.append({
                "type": "partial_trade",
                "description": "Offer combination of cash and trade items",
                "buyer_protection": "Variable - depends on trade items",
                "typical_use": "When you have items the seller might want",
                "price_range": {"min": 0, "max": 0, "target": 0}  # Not directly applicable
            })

        # Time-based payment
        if target_price > 500:
            structures.append({
                "type": "installment_plan",
                "description": "Pay in agreed installments over time",
                "buyer_protection": "Low to Medium - retains some leverage",
                "typical_use": "Higher-value items when immediate payment is difficult",
                "price_range": {"min": min_price, "max": max_price, "target": target_price}
            })

        # Contingent on verification
        if any(word in opportunity_data.get("condition", "").lower()
               for word in ["as is", "where is", "no warranty"]):
            structures.append({
                "type": "inspection_contingent",
                "description": "Make offer contingent on professional inspection",
                "buyer_protection": "High - protects against hidden issues",
                "typical_use": "Vehicles, equipment, or items where condition is uncertain",
                "price_range": {"min": min_price, "max": max_price, "target": target_price}
            })

        return structures

    def _generate_negotiation_insights(self, leverage_analysis: dict, stance: str,
                                     target_range: tuple, opportunity_data: dict) -> List[str]:
        """Generate insights about the negotiation landscape."""
        insights = []
        net_leverate = leverage_analysis["net_leverate"]
        factors = leverage_analysis["factors"]
        min_price, max_price, target_price = target_range

        # Leverage insights
        if abs(net_leverate) >= 20:
            if net_leverate > 0:
                insights.append(f"Strong buyer advantage (+{net_leverate:.0f}) - you have significant negotiating power")
            else:
                insights.append(f"Strong seller advantage ({net_leverate:.0f}) - seller has upper hand in negotiations")
        elif abs(net_leverate) >= 10:
            if net_leverate > 0:
                insights.append(f"Moderate buyer advantage (+{net_leverate:.0f}) - slight edge in negotiations")
            else:
                insights.append(f"Moderate seller advantage ({net_leverate:.0f}) - you'll need to work for concessions")
        else:
            insights.append(f"Relatively balanced negotiation position ({net_leverate:+.0f}) - focus on mutual benefit")

        # Specific factor insights
        if factors["seller_motivation"] >= 10:
            insights.append("High seller motivation detected - good opportunity to negotiate favorable terms")
        elif factors["seller_motivation"] <= -10:
            insights.append("Low seller motivation (or buyer urgency) - seller likely to be firm on price")

        if factors["market_conditions"] >= 10:
            insights.append("Market conditions favor buyer - you may be able to secure below-market price")
        elif factors["market_conditions"] <= -10:
            insights.append("Market conditions favor seller - expect to pay at or above market value")

        if factors["item_condition"] <= -10:
            insights.append("Notable condition issues identified - leverage for price reduction")
        elif factors["item_condition"] >= 10:
            insights.append("Item appears in excellent condition - less room for downward negotiation")

        if factors["timing"] <= -10:
            insights.append("Timing factors work against you - seller may be less flexible")
        elif factors["timing"] >= 10:
            insights.append("Timing factors work in your favor - good opportunity to negotiate")

        if factors["information"] <= -10:
            insights.append("You have good information advantage - reduces uncertainty in negotiation")
        elif factors["information"] >= 10:
            insights.append("Seller appears to have information advantage - verify claims thoroughly")

        # Target range insight
        if target_price > 0:
            current_price = opportunity_data.get("price", 0)
            if current_price > 0:
                discount_pct = ((current_price - target_price) / current_price) * 100
                if discount_pct >= 15:
                    insights.append(f"Target price represents {discount_pct:.0f}% discount from asking")
                elif discount_pct <= -15:
                    insights.append(f"Target price is {abs(discount_pct):.0f}% above asking - may need to increase offer")
                else:
                    diff = target_price - current_price
                    if abs(diff) < 20:
                        insights.append("Target price close to asking - minor adjustment likely needed")
                    else:
                        direction = "above" if diff > 0 else "below"
                        insights.append(f"Target price is ${abs(diff):,.0f} {direction} asking price")

        return insights[:5]  # Limit to top 5 insights

    def _generate_negotiation_recommendations(self, leverage_analysis: dict, stance: str,
                                            target_range: tuple, deal_structure: List[Dict]) -> List[str]:
        """Generate actionable negotiation recommendations."""
        recommendations = []
        net_leverate = leverage_analysis["net_leverate"]
        min_price, max_price, target_price = target_range

        # Overall recommendation based on stance
        if stance == "strong_buyer_favorable":
            recommendations.append("Take an assertive approach - you have considerable leverage")
            recommendations.append(f"Target range: ${min_price:,.0f} - ${max_price:,.0f} (ideal: ${target_price:,.0f})")
            recommendations.append("Start with a strong offer to establish your position")
        elif stance == "moderately_buyer_favorable":
            recommendations.append("Be firm but reasonable - you have some leverage to work with")
            recommendations.append(f"Target range: ${min_price:,.0f} - ${max_price:,.0f} (ideal: ${target_price:,.0f})")
            recommendations.append("Make a solid opening offer and be prepared to justify it")
        elif stance == "neutral":
            recommendations.append("Focus on finding mutually beneficial solution")
            recommendations.append(f"Target range: ${min_price:,.0f} - ${max_price:,.0f} (ideal: ${target_price:,.0f})")
            recommendations.append("Use objective criteria like market value to guide discussions")
        elif stance == "moderately_seller_favorable":
            recommendations.append("Seller has slight advantage - prepare to make competitive offer")
            recommendations.append(f"Target range: ${max_price:,.0f} - ${max_price*1.1:,.0f} (may need to stretch)")
            recommendations.append("Emphasize your seriousness as a buyer and ability to close quickly")
        elif stance == "strong_seller_favorable":
            recommendations.append("Seller has strong position - be prepared to pay closer to asking")
            recommendations.append(f"Consider range: ${max_price:,.0f} - ${max_price*1.2:,.0f} if genuinely interested")
            recommendations.append("Focus on non-price terms if price flexibility is limited")

        # Specific tactical recommendations
        if len(deal_structure) > 1:
            rec_structure = deal_structure[1] if len(deal_structure) > 1 else deal_structure[0]
            if rec_structure["type"] == "escrow_service":
                recommendations.append("Strongly consider using escrow service for protection")
            elif rec_structure["type"] == "inspection_contingent":
                recommendations.append("Make any offer contingent on professional inspection")
            elif rec_structure["type"] == "deposit_balance":
                recommendations.append("Consider small deposit with balance upon verification")

        # Information gathering
        recommendations.append("Research 3-5 comparable sales to strengthen your position")
        recommendations.append("Prepare clear, respectful communication of your offer rationale")

        # Walk away preparation
        recommendations.append("Determine your absolute maximum price before starting negotiation")
        recommendations.append("Be prepared to walk away if terms don't meet your minimum requirements")

        return recommendations[:6]  # Limit to top 6 recommendations

    def _calculate_negotiation_confidence(self, opportunity_data: dict,
                                        leverage_analysis: dict) -> float:
        """Calculate confidence in negotiation guidance."""
        confidence_factors = []
        base_confidence = 0.5

        # Data completeness
        data_points = [
            ("price", opportunity_data.get("price")),
            ("market_value", opportunity_data.get("market_value")),
            ("category", bool(opportunity_data.get("category"))),
            ("condition", bool(opportunity_data.get("condition"))),
            ("description", bool(opportunity_data.get("description"))),
            ("photos_count", opportunity_data.get("photos_count") is not None)
        ]

        available_data = sum(1 for _, value in data_points if value)
        data_ratio = available_data / len(data_points)
        confidence_factors.append(data_ratio * 0.3)  # Up to 0.3 for data completeness

        # Specific high-value indicators
        if opportunity_data.get("price", 0) > 1000:
            confidence_factors.append(0.1)  # Higher confidence for expensive items (more data available)
        elif opportunity_data.get("price", 0) > 100:
            confidence_factors.append(0.05)

        # Listing quality indicators
        photo_count = opportunity_data.get("photos_count", 0)
        if photo_count >= 5:
            confidence_factors.append(0.1)
        elif photo_count >= 3:
            confidence_factors.append(0.05)

        # Description quality
        desc_length = len(opportunity_data.get("description", ""))
        if desc_length > 200:
            confidence_factors.append(0.1)
        elif desc_length > 50:
            confidence_factors.append(0.05)

        # seller information
        seller_info = opportunity_data.get("seller_info", {})
        if seller_info.get("verified", False):
            confidence_factors.append(0.1)
        elif seller_info.get("feedback_count", 0) > 50:
            confidence_factors.append(0.08)
        elif seller_info.get("feedback_count", 0) > 10:
            confidence_factors.append(0.04)

        # Timing information
        if opportunity_data.get("listed_date") or opportunity_data.get("created_at"):
            confidence_factors.append(0.05)

        # Boost confidence if we're using enhanced data from other agents
        using_enhanced_data = self._check_if_using_enhanced_data(opportunity_data)
        if using_enhanced_data:
            confidence_factors.append(0.15)  # Significant boost for using enhanced data

        total_confidence = min(0.95, base_confidence + sum(confidence_factors))
        return max(0.3, total_confidence)  # Don't go below 0.3

    def _check_if_using_enhanced_data(self, opportunity_data: dict) -> bool:
        """Check if we're using enhanced data from other agents."""
        enhanced_indicators = 0
        total_checks = 0

        # Check price agent enhancements
        price_analysis = opportunity_data.get("price", {})
        if isinstance(price_analysis, dict):
            if price_analysis.get("market_value_used") is not None:
                enhanced_indicators += 1
            total_checks += 1
            if price_analysis.get("valuation_factors"):
                enhanced_indicators += 1
            total_checks += 1

        # Check market agent enhancements
        market_analysis = opportunity_data.get("market", {})
        if isinstance(market_analysis, dict):
            insights = market_analysis.get("insights", [])
            if any("timing" in str(i).lower() or "season" in str(i).lower() for i in insights):
                enhanced_indicators += 1
            total_checks += 1
            if any("competition" in str(i).lower() or "alternative" in str(i).lower() for i in insights):
                enhanced_indicators += 1
            total_checks += 1

        # Check trust/risk agent enhancements
        trust_analysis = opportunity_data.get("trust", {})
        risk_analysis = opportunity_data.get("risk", {})
        if isinstance(trust_analysis, dict) or isinstance(risk_analysis, dict):
            # Check for documentation/verification insights
            all_insights = []
            if isinstance(trust_analysis, dict):
                all_insights.extend(trust_analysis.get("insights", []))
            if isinstance(risk_analysis, dict):
                all_insights.extend(risk_analysis.get("risk_details", []))

            if any("documentation" in str(i).lower() or "verification" in str(i).lower() for i in all_insights):
                enhanced_indicators += 1
            total_checks += 1

        return total_checks > 0 and (enhanced_indicators / total_checks) >= 0.5

    def _generate_preparation_checklist(self, opportunity_data: dict,
                                      leverage_analysis: dict) -> List[str]:
        """Generate a preparation checklist for the negotiation."""
        checklist = [
            "Research 3-5 comparable recent sales to establish fair market value",
            "Determine your absolute maximum price (walk-away point)",
            "Identify 2-3 target price points (ideal, reasonable, maximum)",
            "Prepare clear, factual justification for your offer price"
        ]

        # Add item-specific checks
        category = opportunity_data.get("category", "").lower()
        if "vehicle" in category:
            checklist.extend([
                "Obtain vehicle history report (CARFAX, etc.)",
                "Prepare questions about maintenance history and accident history",
                "Consider arranging pre-purchase inspection"
            ])
        elif any(elec in category for elec in ["electronic", "computer", "phone"]):
            checklist.extend([
                "Verify serial number matches documentation if available",
                "Check functionality of all ports, buttons, and features"
            ])
        elif "jewelry" in category or "watch" in category:
            checklist.extend([
                "Request certification and authentication documents",
                "Consider third-party appraisal for high-value pieces"
            ])
        elif "weapon" in category or "firearm" in category:
            checklist.extend([
                "Verify legal requirements for transfer in your jurisdiction",
                "Ensure proper documentation and registration"
            ])

        # Add verification steps based on risk factors
        risk_factors = leverage_analysis["factors"]
        if risk_factors.get("information", 0) >= 10:  # Seller has info advantage
            checklist.extend([
                "Ask for original receipts, documentation, or proof of purchase",
                "Request to see item in person before making any payment"
            ])
        if risk_factors.get("item_condition", 0) <= -10:  # Notable condition issues
            checklist.extend([
                "Prepare specific questions about all noted issues",
                "Ask for close-up photos of any areas of concern"
            ])

        # Payment preparation
        price = opportunity_data.get("price", 0)
        if price > 0:
            max_price = self._calculate_target_price_range(
                price,
                opportunity_data.get("market_value", 0),
                {"factors": {"market_conditions": 0}},
                opportunity_data.get("category", ""),
                opportunity_data.get("brand", ""),
                opportunity_data.get("condition", "")
            )[1]  # Get max price
            if max_price > 200:
                checklist.extend([
                    "Arrange for secure payment method (escrow, certified funds, etc.)",
                    "Avoid wire transfers, money orders, or gift cards for payment"
                ])

        # Final preparations
        checklist.extend([
            "Plan conversation starters and rapport-building topics",
            "Prepare responses to common objections or deflection tactics",
            "Have alternative solutions ready if primary offer is rejected",
            "Schedule sufficient time for negotiation - don't rush the process"
        ])

        return checklist[:12]  # Return top 12 items