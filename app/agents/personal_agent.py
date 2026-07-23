"""Personal Agent: models user preferences, learns from interactions, provides personalized recommendations."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional, List, Tuple
import logging
import json
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class PersonalAgent(BaseAgent):
    """Agent responsible for personalizing recommendations based on user profile and behavior."""

    def __init__(self):
        super().__init__("PersonalAgent")
        # Cache for internal data to avoid repeated processing
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Personalize the opportunity assessment based on user's profile, preferences, and history.

        Expects context to contain user_profile (dict) with fields like:
        - decision_weights
        - behavioral_patterns
        - risk_tolerance_history
        - budget_min/max
        - preferred_categories
        - interaction_history
        - feedback_history

        Returns personalization score and tailored advice.
        """
        self._log_info("Processing personalization analysis")

        user_context = context or {}
        user_profile = user_context.get("user_profile", {})

        # Default neutral score
        personal_score = 50
        notes = []
        tailored_advice = ["No specific user profile provided for personalization"]
        confidence = 0.3
        decision_weights_applied = {}

        # Check if we're getting real data from other agents (enhanced context)
        using_enhanced_data = self._check_if_using_enhanced_data(context or {})
        if using_enhanced_data:
            confidence = 0.6  # Start with higher confidence when using enhanced data
        else:
            confidence = 0.3  # Standard confidence

        if not user_profile:
            return {
                "agent": self.agent_name,
                "personal_score": personal_score,
                "notes": "No user profile provided for personalization",
                "confidence": 0.3,
                "tailored_advice": ["Complete your profile for personalized recommendations"],
                "decision_weights_applied": {}
            }

        # Extract user preferences with defaults
        budget_min = user_profile.get("budget_min")
        budget_max = user_profile.get("budget_max")
        preferred_categories = user_profile.get("preferred_categories", [])
        decision_weights_raw = user_profile.get("decision_weights", "{}")
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")  # conservative, moderate, aggressive
        interaction_history = user_profile.get("interaction_history", [])
        feedback_history = user_profile.get("feedback_history", [])
        user_goals = user_profile.get("goals", [])
        values = user_profile.get("values", [])
        lifestyle_factors = user_profile.get("lifestyle_factors", {})

        # Parse decision_weights if it's a JSON string
        try:
            decision_weights = json.loads(decision_weights_raw) if isinstance(decision_weights_raw, str) else decision_weights_raw
        except (json.JSONDecodeError, TypeError):
            decision_weights = {}

        # Ensure it's a dict
        if not isinstance(decision_weights, dict):
            decision_weights = {}

        # Normalize decision weights if provided
        if decision_weights:
            total_weight = sum(abs(v) for v in decision_weights.values()) or 1
            decision_weights = {k: v/total_weight for k, v in decision_weights.items()}
            decision_weights_applied = decision_weights.copy()
        else:
            # Default weights if none provided
            decision_weights = {
                "price": 0.25,
                "trust": 0.20,
                "risk": 0.15,
                "market": 0.15,
                "discovery": 0.15
            }
            decision_weights_applied = decision_weights.copy()

        # Start with baseline
        personal_score = 50
        adjustment_details = []
        weight_contributions = {}

        # 1. Budget Fit Analysis (enhanced with real market data)
        budget_score, budget_details = await self._assess_budget_fit(
            opportunity_data, budget_min, budget_max, decision_weights.get("price", 0.25)
        )
        personal_score += budget_score
        if budget_details:
            notes.extend(budget_details)
            weight_contributions["budget"] = budget_score

        # 2. Category Preference Alignment
        category_score, category_details = self._assess_category_preference(
            opportunity_data, preferred_categories, decision_weights.get("category", 0.1)
        )
        personal_score += category_score
        if category_details:
            notes.extend(category_details)
            weight_contributions["category_preference"] = category_score

        # 3. Risk Tolerance Alignment (enhanced with real risk data)
        risk_score, risk_details = await self._assess_risk_tolerance_alignment(
            opportunity_data, risk_tolerance, decision_weights.get("risk", 0.15)
        )
        personal_score += risk_score
        if risk_details:
            notes.extend(risk_details)
            weight_contributions["risk_tolerance"] = risk_score

        # 4. Value Alignment (based on user goals and values)
        value_score, value_details = self._assess_value_alignment(
            opportunity_data, user_goals, values, decision_weights.get("values", 0.1)
        )
        personal_score += value_score
        if value_details:
            notes.extend(value_details)
            weight_contributions["value_alignment"] = value_score

        # 5. Lifestyle Compatibility (enhanced with lifestyle/trend data)
        lifestyle_score, lifestyle_details = await self._assess_lifestyle_compatibility(
            opportunity_data, lifestyle_factors
        )
        personal_score += lifestyle_score
        if lifestyle_details:
            notes.extend(lifestyle_details)
            weight_contributions["lifestyle"] = lifestyle_score

        # 6. Historical Preference Learning
        history_score, history_details = self._learn_from_history(
            opportunity_data, interaction_history, feedback_history
        )
        personal_score += history_score
        if history_details:
            notes.extend(history_details)
            weight_contributions["historical_learning"] = history_score

        # 7. Behavioral Pattern Matching
        behavior_score, behavior_details = self._assess_behavioral_fit(
            opportunity_data, user_profile.get("behavioral_patterns", {})
        )
        personal_score += behavior_score
        if behavior_details:
            notes.extend(behavior_details)
            weight_contributions["behavioral_patterns"] = behavior_score

        # Ensure bounds
        personal_score = max(0, min(100, int(personal_score)))

        # Build tailored advice
        tailored_advice = self._build_tailored_advice(
            weight_contributions, notes, user_profile, opportunity_data
        )

        # Calculate confidence based on available user data and enhanced context
        base_confidence = self._calculate_personalization_confidence(user_profile)
        if using_enhanced_data:
            confidence = min(0.95, base_confidence + 0.2)  # Boost confidence with enhanced data
        else:
            confidence = base_confidence

        # Add data quality note
        if using_enhanced_data:
            notes.append("Personalization enhanced with real-time data from other agents")

        return {
            "agent": self.agent_name,
            "personal_score": personal_score,
            "notes": "; ".join(notes) if notes else "Personalization analysis completed",
            "confidence": round(confidence, 2),
            "tailored_advice": tailored_advice,
            "decision_weights_applied": decision_weights_applied,
            "weight_contributions": {k: round(v, 1) for k, v in weight_contributions.items()},
            "user_profile_summary": self._create_user_profile_summary(user_profile),
            "data_quality": {
                "using_enhanced_data": using_enhanced_data,
                "confidence_level": "high" if using_enhanced_data else "moderate"
            }
        }

    async def _assess_budget_fit(self, opportunity_data: dict, budget_min: Optional[float],
                                budget_max: Optional[float], weight: float) -> tuple:
        """Assess how well the opportunity fits within user's budget (enhanced with real market data)."""
        score = 0
        details = []

        price = opportunity_data.get("price")
        if price is None:
            details.append("No price specified - cannot assess budget fit")
            return 0, details

        # Get enhanced market value if available for better budget assessment
        enhanced_market_value = await self._get_enhanced_market_value(opportunity_data)
        if enhanced_market_value is not None and enhanced_market_value > 0:
            # Use enhanced market value for additional context
            details.append(f"Enhanced market value assessment: ${enhanced_market_value:,.0f}")
            if price > enhanced_market_value * 1.5:
                details.append("Price significantly above enhanced market value - consider budget impact")
            elif price < enhanced_market_value * 0.5:
                details.append("Price significantly below enhanced market value - potential value opportunity")

        # Check against budget範囲
        if budget_min is not None and price < budget_min:
            shortage = budget_min - price
            shortage_pct = (shortage / budget_min) * 100
            score -= min(20, int(shortage_pct / 2))  # Up to -20 for being under minimum
            details.append(f"Below minimum budget by ${shortage:,.0f} ({shortage_pct:.0f}%)")
        elif budget_max is not None and price > budget_max:
            excess = price - budget_max
            excess_pct = (excess / budget_max) * 100
            score -= min(25, int(excess_pct / 2))  # Up to -25 for being over maximum
            details.append(f"Above maximum budget by ${excess:,.0f} ({excess_pct:.0f}%)")
        else:
            # Within budget range - calculate how well it fits
            if budget_min is not None and budget_max is not None and budget_max > budget_min:
                # User has a budget range - reward based on position in range
                range_size = budget_max - budget_min
                if range_size > 0:
                    position_in_range = (price - budget_min) / range_size  # 0 to 1
                    # Prefer lower end of range (better value) but not too low (might raise questions)
                    if position_in_range < 0.3:  # Lower third - excellent value
                        score += 15
                        details.append(f"Excellent budget fit - in lower third of range")
                    elif position_in_range < 0.6:  # Middle third - good value
                        score += 10
                        details.append(f"Good budget fit - in middle of range")
                    else:  # Upper third - acceptable but less optimal
                        score += 5
                        details.append(f"Acceptable budget fit - in upper third of range")
                else:
                    # Invalid range
                    score += 0
                    details.append("Within budget range")
            else:
                # Only one budget bound specified
                if budget_max is not None:
                    # Only max specified - reward being under budget
                    usage_pct = (price / budget_max) * 100
                    if usage_pct < 50:
                        score += 15
                        details.append(f"Well under budget - using only {usage_pct:.0f}% of max")
                    elif usage_pct < 80:
                        score += 10
                        details.append(f"Comfortably under budget - using {usage_pct:.0f}% of max")
                    else:
                        score += 5
                        details.append(f"Approaching budget limit - using {usage_pct:.0f}% of max")
                elif budget_min is not None:
                    # Only min specified - reward being above minimum
                    excess_over_min = ((price - budget_min) / budget_min) * 100
                    if excess_over_min < 50:
                        score += 10
                        details.append(f"Just above minimum - good value")
                    elif excess_over_min < 150:
                        score += 5
                        details.append(f"Reasonably above minimum")
                    else:
                        score += 0
                        details.append(f"Significantly above minimum - may indicate premium item")
        else:
            # No budget specified
            details.append("No budget constraints specified in profile")

        # Apply weight
        weighted_score = int(score * weight)
        return weighted_score, details

    async def _get_enhanced_market_value(self, opportunity_data: dict) -> Optional[float]:
        """Get enhanced market value from other agents' analysis."""
        # Check if we already have enhanced data in opportunity_data
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

        # If not available in opportunity_data, return None
        # (Enhanced data comes from other agents through the context)
        return None

    def _assess_category_preference(self, opportunity_data: dict, preferred_categories: List[str],
                                  weight: float) -> tuple:
        """Assess alignment with user's preferred categories."""
        score = 0
        details = []

        if not preferred_categories:
            details.append("No preferred categories specified")
            return 0, details

        category = opportunity_data.get("category", "").lower()
        if not category:
            details.append("No category specified in opportunity")
            return 0, details

        # Check for direct match
        category_match = False
        matched_preference = None
        for pref in preferred_categories:
            if pref.lower() in category or category in pref.lower():
                category_match = True
                matched_preference = pref
                break

        if category_match:
            score += 20
            details.append(f"Matches preferred category: '{matched_preference}'")
        else:
            # Check for related categories
            related_matches = []
            category_terms = category.split()
            for pref in preferred_categories:
                pref_terms = pref.lower().split()
                # Check for any term overlap
                if any(term in pt for pt in pref_terms for term in category_terms):
                    related_matches.append(pref)

            if related_matches:
                score += 10
                details.append(f"Related to preferred categories: {', '.join(related_matches[:2])}")
            else:
                score -= 10
                details.append(f"Does not match preferred categories ({', '.join(preferred_categories[:3])}...)")

        # Apply weight
        weighted_score = int(score * weight)
        return weighted_score, details

    async def _assess_risk_tolerance_alignment(self, opportunity_data: dict, risk_tolerance: str,
                                               weight: float) -> tuple:
        """Assess how well the opportunity's risk level matches user's tolerance (enhanced with real risk data)."""
        score = 0
        details = []

        # Get enhanced risk assessment from risk agent if available
        risk_analysis = opportunity_data.get("risk", {})
        if isinstance(risk_analysis, dict) and "risk_level" in risk_analysis:
            # Use the actual risk level from risk agent
            risk_level = risk_analysis.get("risk_level", "moderate").lower()
            risk_score_val = risk_analysis.get("risk_score", 50)
            details.append(f"Risk agent assessment: {risk_level} (score: {risk_score_val})")
        else:
            # Fallback to original estimation
            risk_indicators = []
            risk_level = "moderate"  # Default

            # Check for high-risk indicators
            high_risk_indicators = [
                "as is", "where is", "no returns", "final sale", "salvage", "rebuilt",
                "accident", "damage", "not working", "broken", "defective", "for parts"
            ]

            opportunity_text = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()
            high_risk_count = sum(1 for indicator in high_risk_indicators if indicator in opportunity_text)

            # Check for low-risk indicators
            low_risk_indicators = [
                "warranty", "guarantee", "return policy", "certified", "authenticated",
                "service records", "maintenance history", "clean title", "no accidents"
            ]

            low_risk_count = sum(1 for indicator in low_risk_indicators if indicator in opportunity_text)

            # Estimate risk level
            if high_risk_count >= 3:
                risk_level = "high"
            elif high_risk_count >= 1:
                risk_level = "medium_high"
            elif low_risk_count >= 2:
                risk_level = "low"
            elif low_risk_count >= 1:
                risk_level = "medium_low"
            else:
                risk_level = "moderate"

        # Compare with user's risk tolerance
        tolerance_map = {
            "conservative": ["very_low", "low", "medium_low"],
            "moderate": ["low", "medium_low", "moderate", "medium_high"],
            "aggressive": ["medium", "medium_high", "high", "very_high"]
        }

        user_tolerance_levels = tolerance_map.get(risk_tolerance, ["moderate"])

        if risk_level in user_tolerance_levels:
            score += 15
            details.append(f"Risk level ({risk_level}) matches your {risk_tolerance} tolerance")
        else:
            # Check if it's close
            risk_levels_ordered = ["very_low", "low", "medium_low", "moderate", "medium_high", "high", "very_high"]
            try:
                user_idx = risk_levels_ordered.index(user_tolerance_levels[0]) if user_tolerance_levels else 3
                actual_idx = risk_levels_ordered.index(risk_level) if risk_level in risk_levels_ordered else 3
                diff = abs(actual_idx - user_idx)

                if diff == 1:
                    score += 5
                    details.append(f"Risk level ({risk_level}) is close to your {risk_tolerance} tolerance")
                elif diff == 2:
                    score -= 5
                    details.append(f"Risk level ({risk_level}) is somewhat different from your preference")
                else:
                    score -= 15
                    details.append(f"Risk level ({risk_level}) poorly matches your {risk_tolerance} tolerance")
            except ValueError:
                score += 0
                details.append("Unable to precisely match risk levels")

        # Apply weight
        weighted_score = int(score * weight)
        return weighted_score, details

    def _assess_value_alignment(self, opportunity_data: dict, goals: List[str],
                              values: List[str], weight: float) -> tuple:
        """Assess alignment with user's goals and values."""
        score = 0
        details = []

        opportunity_text = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()

        # Check alignment with goals
        goal_matches = 0
        if goals:
            for goal in goals:
                goal_lower = goal.lower()
                # Direct match
                if goal_lower in opportunity_text:
                    goal_matches += 1
                    details.append(f"Aligns with goal: '{goal}'")
                else:
                    # Check for related concepts
                    goal_words = set(goal_lower.split())
                    opp_words = set(opportunity_text.split())
                    if goal_words & opp_words:  # Intersection
                        goal_matches += 1
                        details.append(f"Related to goal: '{goal}'")

        # Check alignment with values
        value_matches = 0
        if values:
            value_keywords = {
                "sustainability": ["eco", "green", "sustainable", "environmental", "recycled", "used", "secondhand"],
                "quality": ["quality", "durable", "long-lasting", "premium", "high-end", "professional"],
                "value": ["value", "budget", "affordable", "economical", "cost-effective", "discount"],
                "innovation": ["new", "latest", "cutting-edge", "innovative", "advanced", "state-of-the-art"],
                "tradition": ["classic", "vintage", "traditional", "heritage", "timeless", "antique"],
                "community": ["local", "community", "neighborhood", "nearby", "close", "walkable"],
                "convenience": ["convenient", "easy", "simple", "plug-and-play", "ready-to-use", "assembled"],
                "health": ["fitness", "exercise", "health", "wellness", "active", "sport"],
                "learning": ["educational", "learning", "study", "book", "course", "training"],
                "creativity": ["creative", "art", "design", "craft", "make", "build", "create"]
            }

            for value in values:
                value_lower = value.lower()
                if value_lower in value_keywords:
                    keywords = value_keywords[value_lower]
                    if any(keyword in opportunity_text for keyword in keywords):
                        value_matches += 1
                        details.append(f"Aligns with value: '{value}'")
                else:
                    # Direct match attempt
                    if value_lower in opportunity_text:
                        value_matches += 1
                        details.append(f"Aligns with value: '{value}'")

        # Calculate score based on matches
        total_possible = max(len(goals), 1) + max(len(values), 1)
        if total_possible > 0:
            match_ratio = (goal_matches + value_matches) / total_possible
            score = int(match_ratio * 30)  # Up to 30 points for strong alignment

            if goal_matches > 0 and value_matches > 0:
                details.append(f"Strong alignment with both goals ({goal_matches}) and values ({value_matches})")
            elif goal_matches > 0:
                details.append(f"Good alignment with goals ({goal_matches})")
            elif value_matches > 0:
                details.append(f"Good alignment with values ({value_matches})")
            else:
                details.append("Limited alignment with specified goals and values")
        else:
            details.append("No specific goals or values specified in profile")

        # Apply weight
        weighted_score = int(score * weight)
        return weighted_score, details

    async def _assess_lifestyle_compatibility(self, opportunity_data: dict,
                                            lifestyle_factors: Dict[str, Any]) -> tuple:
        """Assess how well the opportunity fits user's lifestyle (enhanced with trend data)."""
        score = 0
        details = []

        if not lifestyle_factors:
            details.append("No lifestyle factors specified")
            return 0, details

        opportunity_text = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()
        location = opportunity_data.get("location", "").lower()

        # Get enhanced lifestyle/trend data if available
        lifestyle_enhancement = await self._get_lifestyle_enhancement(opportunity_data)
        if lifestyle_enhancement:
            enhancement_score = lifestyle_enhancement.get("score_adjustment", 0)
            score += enhancement_score
            details.append(f"Lifestyle/trend enhancement: {lifestyle_enhancement.get('assessment', 'N/A')} ({enhancement_score:+d})")

        # Check various lifestyle factors
        lifestyle_matches = 0
        total_factors = len(lifestyle_factors)

        # Living situation
        if "living_situation" in lifestyle_factors:
            living_situation = lifestyle_factors["living_situation"].lower()
            if "apartment" in living_situation or "condo" in living_situation:
                # Check for space-friendly items
                if any(word in opportunity_text for word in ["compact", "small", "space-saving", "apartment"]):
                    lifestyle_matches += 1
                    details.append("Suitable for apartment/condo living")
                elif any(word in opportunity_text for word in ["large", "bulky", "industrial", "commercial"]):
                    # Penalty for large items in small spaces
                    pass
            elif "house" in living_situation:
                # More flexible for houses
                lifestyle_matches += 1
                details.append("Compatible with house living")

        # Transportation needs
        if "transportation" in lifestyle_factors:
            transport_needs = lifestyle_factors["transportation"].lower()
            if "public transit" in transport_needs or "no car" in transport_needs:
                # Check if item is easily transportable
                if any(word in opportunity_text for word in ["portable", "lightweight", "compact", "carry"]):
                    lifestyle_matches += 1
                    details.append("Easy to transport without car")
                elif any(word in opportunity_text for word in ["vehicle", "car", "truck", "large", "heavy"]):
                    # Likely difficult without personal vehicle
                    pass
            elif "long commute" in transport_needs:
                if any(word in opportunity_text for word in ["audio", "podcast", "language", "learning"]):
                    lifestyle_matches += 1
                    details.append("Good for commuting/time utilization")

        # Family situation
        if "family_status" in lifestyle_factors:
            family_status = lifestyle_factors["family_status"].lower()
            if "children" in family_status or "kids" in family_status:
                if any(word in opportunity_text for word in ["family", "kid", "child", "educational", "toy", "game"]):
                    lifestyle_matches += 1
                    details.append("Family/child-friendly")
                elif any(word in opportunity_text for word in ["fragile", "delicate", "expensive", "antique"]):
                    # Might be problematic with kids
                    pass
            elif "single" in family_status:
                # More flexible
                lifestyle_matches += 1
                details.append("Suits single lifestyle")

        # Activity level
        if "activity_level" in lifestyle_factors:
            activity_level = lifestyle_factors["activity_level"].lower()
            if "active" in activity_level or "fitness" in activity_level:
                if any(word in opportunity_text for word in ["sport", "exercise", "fitness", "outdoor", "gym"]):
                    lifestyle_matches += 1
                    details.append("Matches active lifestyle")
            elif "sedentary" in activity_level or "low activity" in activity_level:
                if any(word in opportunity_text for word in ["book", "reading", "movie", "game", "electronics"]):
                    lifestyle_matches += 1
                    details.append("Suits more sedentary lifestyle")

        # Work requirements
        if "work_type" in lifestyle_factors:
            work_type = lifestyle_factors["work_type"].lower()
            if "remote" in work_type or "home office" in work_type:
                if any(word in opportunity_text for word in ["desk", "chair", "monitor", "computer", "office"]):
                    lifestyle_matches += 1
                    details.append("Suitable for home office/work from home")
            elif "creative" in work_type or "design" in work_type:
                if any(word in opportunity_text for word in ["design", "art", "creative", "studio", "software"]):
                    lifestyle_matches += 1
                    details.append("Aligns with creative work needs")
            elif "technical" in work_type or "engineering" in work_type:
                if any(word in opportunity_text for word in ["tool", "equipment", "technical", "lab", "measurement"]):
                    lifestyle_matches += 1
                    details.append("Matches technical/professional requirements")

        # Calculate score
        if total_factors > 0:
            match_ratio = min(1.0, lifestyle_matches / total_factors)
            score += int((match_ratio - 0.5) * 40)  # -20 to +20 range
            if score > 0:
                details.append(f"Good lifestyle alignment ({lifestyle_matches}/{total_factors} factors matched)")
            elif score < 0:
                details.append(f"Poor lifestyle alignment ({lifestyle_matches}/{total_factors} factors matched)")
            else:
                details.append(f"Neutral lifestyle alignment ({lifestyle_matches}/{total_factors} factors matched)")

        # Apply weight (we'll use a default weight of 0.1 since this wasn't in original weights)
        weighted_score = int(score * 0.1)
        return weighted_score, details

    async def _get_lifestyle_enhancement(self, opportunity_data: dict) -> Optional[dict]:
        """Get lifestyle enhancement from trend/lifestyle data."""
        # Check if we have lifestyle insights from market agent
        market_analysis = opportunity_data.get("market", {})
        if isinstance(market_analysis, dict):
            insights = market_analysis.get("insights", [])
            for insight in insights:
                if any(word in insight.lower() for word in ["lifestyle", "trend", "fashion", "popular", "demand"]):
                    # Determine if it's positive or negative for lifestyle fit
                    if any(word in insight.lower() for word in ["growing", "popular", "increasing", "trending up"]):
                        return {"score_adjustment": 5, "assessment": insight}
                    elif any(word in insight.lower() for word in ["declining", "decreasing", "falling out", "trending down"]):
                        return {"score_adjustment": -5, "assessment": insight}
                    else:
                        return {"score_adjustment": 0, "assessment": insight}

        # Check if we have values analysis from other agents
        # (This would be circular if we checked our own analysis, so we skip it)

        return None

    def _learn_from_history(self, opportunity_data: dict,
                          interaction_history: List[Dict],
                          feedback_history: List[Dict]) -> tuple:
        """Learn from user's past interactions and feedback."""
        score = 0
        details = []

        if not interaction_history and not feedback_history:
            details.append("No interaction or feedback history available for learning")
            return 0, details

        opportunity_text = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()
        opportunity_category = opportunity_data.get("category", "").lower()
        opportunity_brand = opportunity_data.get("brand", "").lower()

        # Analyze positive interactions
        positive_signals = 0
        negative_signals = 0

        # Check interaction history
        for interaction in interaction_history[-20:]:  # Look at recent interactions
            if not isinstance(interaction, dict):
                continue

            action = interaction.get("action", "").lower()
            item_id = interaction.get("item_id", "")
            item_details = str(interaction.get("item_details", "")).lower()

            # Positive actions
            if action in ["viewed", "favorited", "shared", "contacted_seller"]:
                # Check similarity to current opportunity
                similarity_score = self._calculate_similarity(opportunity_text, item_details)
                if similarity_score > 0.3:  # Somewhat similar
                    if action == "favorited":
                        positive_signals += 2
                    elif action == "contacted_seller":
                        positive_signals += 1.5
                    else:
                        positive_signals += 1

            # Negative actions
            elif action in ["ignored", "skipped", "reported"]:
                similarity_score = self._calculate_similarity(opportunity_text, item_details)
                if similarity_score > 0.3:
                    if action == "reported":
                        negative_signals += 2
                    else:
                        negative_signals += 1

        # Check feedback history
        for feedback in feedback_history[-20:]:  # Look at recent feedback
            if not isinstance(feedback, dict):
                continue

            rating = feedback.get("rating", 0)  # Assuming 1-5 scale
            item_id = feedback.get("item_id", "")
            item_details = str(feedback.get("item_details", "")).lower()
            feedback_text = str(feedback.get("feedback", "")).lower()

            # Positive feedback
            if rating >= 4 or any(word in feedback_text for word in ["great", "excellent", "love", "perfect", "recommend"]):
                similarity_score = self._calculate_similarity(opportunity_text, item_details)
                if similarity_score > 0.3:
                    positive_signals += rating / 2  # Scale rating to contribution

            # Negative feedback
            elif rating <= 2 or any(word in feedback_text for word in ["bad", "poor", "disappointed", "issue", "problem"]):
                similarity_score = self._calculate_similarity(opportunity_text, item_details)
                if similarity_score > 0.3:
                    negative_signals += (5 - rating) / 2  # Invert and scale

        # Calculate net sentiment
        net_sentiment = positive_signals - negative_signals
        if net_sentiment > 3:
            score += 15
            details.append("Strong positive history with similar items")
        elif net_sentiment > 0:
            score += 8
            details.append("Positive history with similar items")
        elif net_sentiment < -3:
            score -= 15
            details.append("Strong negative history with similar items - exercise caution")
        elif net_sentiment < 0:
            score -= 8
            details.append("Negative history with similar items")

        # Check for brand preferences from history
        if opportunity_brand:
            brand_preference_score = 0
            brand_mentions = 0
            positive_brand_mentions = 0

            for interaction in interaction_history:
                if not isinstance(interaction, dict):
                    continue
                item_details = str(interaction.get("item_details", "")).lower()
                if opportunity_brand in item_details:
                    brand_mentions += 1
                    action = interaction.get("action", "").lower()
                    if action in ["favorited", "contacted_seller", "purchased"]:
                        positive_brand_mentions += 1

            if brand_mentions > 0:
                preference_ratio = positive_brand_mentions / brand_mentions
                if preference_ratio > 0.7 and brand_mentions >= 2:
                    score += 10
                    details.append(f"Positive history with brand '{opportunity_brand}'")
                elif preference_ratio < 0.3 and brand_mentions >= 2:
                    score -= 10
                    details.append(f"Negative history with brand '{opportunity_brand}'")

        # Apply learning rate (how much we trust historical patterns)
        total_interactions = len(interaction_history) + len(feedback_history)
        learning_factor = min(0.5, total_interactions / 50)  # Max 0.5 after 50 interactions
        final_score = int(score * (0.5 + learning_factor))  # Base 0.5 + learning

        if total_interactions == 0:
            details.append("No historical data to learn from")
        elif total_interactions < 10:
            details.append("Limited historical data - preferences still developing")

        return final_score, details

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (0-1 scale)."""
        if not text1 or not text2:
            return 0.0

        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(interaction) / len(union) if union else 0.0

    def _assess_behavioral_fit(self, opportunity_data: dict,
                             behavioral_patterns: Dict[str, Any]) -> tuple:
        """Assess how well the opportunity matches user's behavioral patterns."""
        score = 0
        details = []

        if not behavioral_patterns:
            details.append("No behavioral patterns specified")
            return 0, details

        opportunity_text = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()
        price = opportunity_data.get("price", 0)

        # Check purchasing frequency preferences
        if "purchase_frequency" in behavioral_patterns:
            freq = behavioral_patterns["purchase_frequency"].lower()
            if "impulse_buyer" in freq:
                # Impulse buyers might like lower-cost, immediate gratification items
                if price < 50:
                    score += 5
                    details.append("Low-cost item suits impulse buying tendency")
                elif price > 200:
                    score -= 5
                    details.append("High-cost item may not suit impulse buying pattern")
            elif "planned_buyer" in freq:
                # Planned buyers research and wait
                if price > 100:
                    score += 5
                    details.append("Higher-cost item suits planned purchasing behavior")
                else:
                    score -= 3
                    details.append("Very low-cost item may not warrant planned approach")

        # Check decision speed preference
        if "decision_speed" in behavioral_patterns:
            speed = behavioral_patterns["decision_speed"].lower()
            if "quick" in speed:
                # Prefer quick decisions - simpler items, less research needed
                complexity_indicators = ["complex", "technical", "specialized", "professional", "advanced"]
                complexity_count = sum(1 for ind in complexity_indicators if ind in opportunity_text)
                if complexity_count == 0:
                    score += 5
                    details.append("Simple item suits quick decision preference")
                else:
                    score -= 3
                    details.append("Complex item may require more research than preferred")
            elif "research_oriented" in speed:
                # Like to research - complex/technical items may be preferred
                complexity_indicators = ["technical", "professional", "specification", "detail", "advanced"]
                complexity_count = sum(1 for ind in complexity_indicators if ind in opportunity_text)
                if complexity_count >= 2:
                    score += 5
                    details.append("Technical nature suits research-oriented approach")
                else:
                    score -= 3
                    details.append("Simple item may not satisfy research preference")

        # Check budgeting style
        if "budgeting_style" in behavioral_patterns:
            budget_style = behavioral_patterns["budgeting_style"].lower()
            if "strict" in budget_style:
                # Strict budgeters dislike unexpected costs
                if any(word in opportunity_text for word in ["as is", "where is", "no warranty"]):
                    score -= 8
                    details.append("'As-is' sale conflicts with strict budgeting preference")
                elif any(word in opportunity_text for word in ["warranty", "guarantee", "return"]):
                    score += 5
                    details.append("Warranty/guarantee aligns with strict budgeting")
            elif "flexible" in budget_style:
                # Flexible budgeters are more open to negotiation
                if any(word in opportunity_text for word in ["negotiable", "obo", "best offer"]):
                    score += 3
                    details.append("Negotiable price suits flexible budgeting style")

        # Check social preferences
        if "social_preference" in behavioral_patterns:
            social_pref = behavioral_patterns["social_preference"].lower()
            if "avoid_crowds" in social_pref:
                # Prefer online or low-contact transactions
                if any(word in opportunity_text for word in ["shipping", "delivery", "mail", "ship"]):
                    shipping_cost = "free shipping" in opportunity_text or "shipping included" in opportunity_text
                    if shipping_cost:
                        score += 5
                        details.append("Free shipping suits preference for minimal contact")
                    else:
                        score += 2
                        details.append("Shipping available suits low-contact preference")
                elif any(word in opportunity_text for word in ["meet", "pickup", "in person"]):
                    score -= 5
                    details.append("In-person pickup conflicts with crowd avoidance preference")
            elif "social_buyer" in social_pref:
                # Enjoys social aspect of shopping
                if any(word in opportunity_text for word in ["meet", "pickup", "in person", "local", "handshake"]):
                    score += 5
                    details.append("In-person transaction suits social preference")
                elif any(word in opportunity_text for word in ["shipping", "delivery"]):
                    score -= 3
                    details.append("Shipping-only limits social interaction")

        return score, details

    def _check_if_using_enhanced_data(self, context: dict) -> bool:
        """Check if we're getting enhanced data from other agents."""
        # Check if any of the agent analyses show high confidence (indicating real data)
        agents_to_check = ["price", "trust", "risk", "market"]
        enhanced_indicators = 0
        total_checked = 0

        for agent_key in agents_to_check:
            analysis = context.get(agent_key, {})
            if isinstance(analysis, dict):
                confidence = analysis.get("confidence", 0.5)
                if confidence > 0.75:  # High confidence threshold indicates real data
                    enhanced_indicators += 1
                total_checked += 1

        # Also check for specific enhanced data fields
        price_analysis = context.get("price", {})
        if isinstance(price_analysis, dict):
            if price_analysis.get("market_value_used") is not None:
                enhanced_indicators += 1
            total_checked += 1

        risk_analysis = context.get("risk", {})
        if isinstance(risk_analysis, dict):
            if "risk_level" in risk_analysis:
                enhanced_indicators += 1
            total_checked += 1

        market_analysis = context.get("market", {})
        if isinstance(market_analysis, dict):
            insights = market_analysis.get("insights", [])
            if insights:  # Having insights suggests enhanced analysis
                enhanced_indicators += 1
            total_checked += 1

        return total_checked > 0 and (enhanced_indicators / total_checked) >= 0.5

    def _build_tailored_advice(self, weight_contributions: Dict[str, float],
                             notes: List[str], user_profile: Dict[str, Any],
                             opportunity_data: dict) -> List[str]:
        """Build tailored advice based on analysis results."""
        advice = []

        # Start with general advice if no specific insights
        if not weight_contributions and not notes:
            advice.append("Complete your profile to receive personalized recommendations")
            advice.append("Consider how this opportunity aligns with your goals and budget")
            return advice

        # Add advice based on strongest positive factors
        positive_factors = [(k, v) for k, v in weight_contributions.items() if v > 5]
        positive_factors.sort(key=lambda x: x[1], reverse=True)

        for factor, value in positive_factors[:3]:  # Top 3 positive factors
            if factor == "budget":
                advice.append("This opportunity fits well within your budget parameters")
            elif factor == "category_preference":
                advice.append("Aligns with your preferred categories - worth serious consideration")
            elif factor == "risk_tolerance":
                advice.append("Risk level matches your comfort zone")
            elif factor == "value_alignment":
                advice.append("Aligns well with your personal goals and values")
            elif factor == "lifestyle":
                advice.append("Good fit for your lifestyle and living situation")
            elif factor == "historical_learning":
                advice.append("Similar items have historically received positive feedback from you")
            elif factor == "behavioral_patterns":
                advice.append("Matches your typical decision-making and purchasing patterns")

        # Add advice based on concerning negative factors
        negative_factors = [(k, v) for k, v in weight_contributions.items() if v < -5]
        negative_factors.sort(key=lambda x: x[1])  # Most negative first

        for factor, value in negative_factors[:2]:  # Top 2 concerning factors
            if factor == "budget":
                advice.append("Carefully consider if this fits your budget - may require adjustment elsewhere")
            elif factor == "category_preference":
                advice.append("Doesn't match your usual preferences - consider if you're open to trying something new")
            elif factor == "risk_tolerance":
                advice.append("Risk level may be outside your comfort zone - proceed with extra caution")
            elif factor == "value_alignment":
                advice.append("Consider how this aligns with your long-term goals and values")
            elif factor == "lifestyle":
                advice.append("Think about how this would fit into your daily life and living situation")
            elif factor == "historical_learning":
                advice.append("Your past experience with similar items suggests caution may be warranted")
            elif factor == "behavioral_patterns":
                advice.append("May not align with your typical approach - consider if this situation is different")

        # Add contextual advice
        price = opportunity_data.get("price", 0)
        if price > 0:
            budget_max = user_profile.get("budget_max")
            if budget_max and price > budget_max * 0.8:
                advice.append("This is a significant portion of your budget - ensure it's a priority")
            elif budget_max and price < budget_max * 0.3:
                advice.append("Relatively low cost within your budget - lower risk opportunity")

        # Add enhancement advice if using real data
        if self._check_if_using_enhanced_data(context or {}):
            advice.append("Recommendations enhanced with real-time market data for greater accuracy")

        # Ensure we have advice
        if not advice:
            advice = ["Consider how this opportunity fits your overall objectives and constraints"]

        return advice[:6]  # Limit to top 6 pieces of advice

    def _calculate_personalization_confidence(self, user_profile: Dict[str, Any]) -> float:
        """Calculate confidence in personalization based on user profile completeness."""
        confidence_factors = []
        base_confidence = 0.3

        # Profile completeness
        profile_sections = [
            ("budget", bool(user_profile.get("budget_min") is not None or user_profile.get("budget_max") is not None)),
            ("categories", bool(user_profile.get("preferred_categories"))),
            ("decision_weights", bool(user_profile.get("decision_weights"))),
            ("risk_tolerance", bool(user_profile.get("risk_tolerance"))),
            ("goals", bool(user_profile.get("goals"))),
            ("values", bool(user_profile.get("values"))),
            ("lifestyle", bool(user_profile.get("lifestyle_factors"))),
            ("history", bool(user_profile.get("interaction_history") or user_profile.get("feedback_history"))),
            ("behavioral", bool(user_profile.get("behavioral_patterns")))
        ]

        completed_sections = sum(1 for _, complete in profile_sections if complete)
        section_ratio = completed_sections / len(profile_sections)
        confidence_factors.append(section_ratio * 0.4)  # Up to 0.4 for profile completeness

        # Data richness
        if user_profile.get("interaction_history"):
            history_length = len(user_profile["interaction_history"])
            history_factor = min(0.2, history_length / 50)  # Up to 0.2 for 50+ interactions
            confidence_factors.append(history_factor)

        if user_profile.get("feedback_history"):
            feedback_length = len(user_profile["feedback_history"])
            feedback_factor = min(0.15, feedback_length / 30)  # Up to 0.15 for 30+ feedback items
            confidence_factors.append(feedback_factor)

        # Recent activity
        # Would check timestamps in real implementation - simplified here
        if user_profile.get("last_updated"):
            # Assume recent update if field exists
            confidence_factors.append(0.1)

        total_confidence = min(0.95, base_confidence + sum(confidence_factors))
        return max(0.3, total_confidence)  # Don't go below 0.3

    def _create_user_profile_summary(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the user profile for transparency."""
        summary = {
            "has_budget": bool(user_profile.get("budget_min") is not None or user_profile.get("budget_max") is not None),
            "budget_range": {
                "min": user_profile.get("budget_min"),
                "max": user_profile.get("budget_max")
            } if user_profile.get("budget_min") is not None or user_profile.get("budget_max") is not None else None,
            "preferred_categories_count": len(user_profile.get("preferred_categories", [])),
            "has_decision_weights": bool(user_profile.get("decision_weights")),
            "risk_tolerance": user_profile.get("risk_tolerance", "unspecified"),
            "goals_count": len(user_profile.get("goals", [])),
            "values_count": len(user_profile.get("values", [])),
            "has_lifestyle_factors": bool(user_profile.get("lifestyle_factors")),
            "history_size": len(user_profile.get("interaction_history", [])) + len(user_profile.get("feedback_history", [])),
            "has_behavioral_patterns": bool(user_profile.get("behavioral_patterns")),
            "profile_updated": user_profile.get("last_updated", "unknown")
        }
        return summary