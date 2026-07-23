"""Risk Agent: assesses risks associated with opportunities."""

from app.agents.base_agent import BaseAgent
from typing import Dict[Any, Any], Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Agent responsible for assessing risks associated with opportunities."""

    def __init__(self):
        super().__init__("RiskAgent")

        # Risk weights for different factors (higher = more risky)
        self.risk_weights = {
            "price_anomaly": 0.20,
            "seller_behavior": 0.15,
            "item_condition": 0.15,
            "transaction_details": 0.15,
            "external_factors": 0.10,
            "documentation": 0.10,
            "category_risk": 0.05,
            "timing": 0.05,
            "communication": 0.05
        }

        # High-risk categories (base risk score addition)
        self.high_risk_categories = {
            "jewelry": 15,
            "watches": 15,
            "electronics": 10,
            "phones": 10,
            "computers": 10,
            "vehicles": 12,
            "collectibles": 8,
            "art": 8,
            "luxury_goods": 12,
            "designer": 15,
            "handbags": 12,
            "shoes": 10
        }

        # Low-risk categories (risk reduction)
        self.low_risk_categories = {
            "books": -5,
            "clothing": -3,
            "home_goods": -2,
            "sports": -3,
            "toys": -2,
            "games": -3,
            "musical_instruments": -4
        }

        # Payment method risk levels
        self.payment_risk = {
            "wire_transfer": 25,
            "money_order": 20,
            "gift_card": 30,
            "cryptocurrency": 25,
            "cash": 15,
            "paypal": 5,
            "credit_card": 3,
            "escrow": -10,  # Actually reduces risk
            "bank_transfer": 15
        }

        # Communication red flags
        self.communication_red_flags = [
            "urgent", "act now", "limited time", "don't miss", "hurry",
            "price firm", "no negotiation", "must sell today",
            "moving abroad", "leaving country", "deploying",
            "divorce", "bankruptcy", "financial trouble",
            "deceased relative", "inheritance", "estate sale",
            "below market", "way below market", "priced to sell",
            "first come first served", "no holds", "serious buyers only",
            "wire transfer only", "no paypal", "cash only",
            "meet in parking lot", "meet at police station"
        ]

        # Positive trust indicators
        self.trust_indicators = [
            "return policy", "warranty", "guarantee", "authentic",
            "genuine", "original", "box included", "papers included",
            "service records", "maintenance history", "clean title",
            "no accidents", "smoke free", "pet free", "recent service",
            "new tires", "brakes", "battery", "inspection", "appraisal",
            "certificate", "appraisal", "grading", "authentication"
        ]

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identify risks such as fraud, volatility, hidden costs, etc.

        Returns risk score (lower is better risk), risk factors, and mitigation suggestions.
        """
        self._log_info("Processing risk analysis")

        # Initialize risk assessment
        risk_score = 50  # Start with neutral risk (0=low risk, 100=high risk)
        risk_factors = []
        risk_details = []
        mitigation_suggestions = []

        # Extract relevant data
        price = opportunity_data.get("price")
        title = opportunity_data.get("title", "").lower()
        description = opportunity_data.get("description", "").lower()
        seller_info = opportunity_data.get("seller_info", {})
        category = opportunity_data.get("category", "").lower()
        brand = opportunity_data.get("brand", "").lower()
        condition = opportunity_data.get("condition", "").lower()
        location = opportunity_data.get("location", "").lower()
        payment_terms = opportunity_data.get("payment_terms", "").lower()
        shipping_info = opportunity_data.get("shipping_info", "").lower()
        listed_date_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        communication_history = opportunity_data.get("communication_history", [])
        photos_count = opportunity_data.get("photos_count", 0)
        video_available = opportunity_data.get("video_available", False)

        # 1. Price Anomaly Analysis (internal)
        price_risk, price_factors, price_mitigations = self._assess_price_anomaly_risk_internal(
            price, title, description, opportunity_data
        )
        risk_score += price_risk
        risk_factors.extend([("price_anomaly", f) for f in price_factors])
        risk_details.extend(price_factors)
        mitigation_suggestions.extend(pm for pm in price_mitigations if pm not in mitigation_suggestions)

        # 2. Seller Behavior Analysis
        seller_risk, seller_factors, seller_mitigations = self._assess_seller_behavior_risk(
            seller_info, communication_history, price
        )
        risk_score += seller_risk
        risk_factors.extend([("seller_behavior", f) for f in seller_factors])
        risk_details.extend(seller_factors)
        mitigation_suggestions.extend(sm for sm in seller_mitigations if sm not in mitigation_suggestions)

        # 3. Item Condition Risk
        condition_risk, condition_factors, condition_mitigations = self._assess_item_condition_risk(
            condition, title, description, photos_count, video_available
        )
        risk_score += condition_risk
        risk_factors.extend([("item_condition", f) for f in condition_factors])
        risk_details.extend(condition_factors)
        mitigation_suggestions.extend(cm for cm in condition_mitigations if cm not in mitigation_suggestions)

        # 4. Transaction Details Risk
        transaction_risk, transaction_factors, transaction_mitigations = self._assess_transaction_details_risk(
            payment_terms, shipping_info, location
        )
        risk_score += transaction_risk
        risk_factors.extend([("transaction_details", f) for f in transaction_factors])
        risk_details.extend(transaction_factors)
        mitigation_suggestions.extend(tm for tm in transaction_mitigations if tm not in mitigation_suggestions)

        # 5. External Factors Risk (internal)
        external_risk, external_factors, external_mitigations = self._assess_external_factors_risk_internal(
            category, brand, listed_date_str, opportunity_data
        )
        risk_score += external_risk
        risk_factors.extend([("external_factors", f) for f in external_factors])
        risk_details.extend(external_factors)
        mitigation_suggestions.extend(em for em in external_mitigations if em not in mitigation_suggestions)

        # 6. Documentation Risk
        doc_risk, doc_factors, doc_mitigations = self._assess_documentation_risk(
            opportunity_data
        )
        risk_score += doc_risk
        risk_factors.extend([("documentation", f) for f in doc_factors])
        risk_details.extend(doc_factors)
        mitigation_suggestions.extend(dm for dm in doc_mitigations if dm not in mitigation_suggestions)

        # 7. Category Risk
        category_risk = self._assess_category_risk(category)
        risk_score += category_risk
        if category_risk != 0:
            risk_factors.append(("category_risk", f"Category risk: {category_risk:+d}"))
            if category_risk > 0:
                risk_details.append(f"High-risk category ({category}) adds {category_risk} points")
            else:
                risk_details.append(f"Low-risk category ({category}) reduces risk by {abs(category_risk)} points")

        )
risk_score += category_risk
        if category_risk != 0:
            risk_factors.append(("category_risk", f"Category risk: {category_risk:+d}"))
            if category_risk > 0:
                risk_details.append(f"High-risk category ({category}) adds {category_risk} points")
            else:
                risk_details.append(f"Low-risk category ({category}) reduces risk by {abs(category_risk)} points")

        # 8. Timing Risk
        timing_risk, timing_factors, timing_mitigations = self._assess_timing_risk(listed_date_str)
        risk_score += timing_risk
        risk_factors.extend([("timing", f) for f in timing_factors])
        risk_details.extend(timing_factors)
        mitigation_suggestions.extend(tm for tm in timing_mitigations if tm not in mitigation_suggestions)

        # 9. Communication Risk
        comm_risk, comm_factors, comm_mitigations = self._assess_communication_risk(
            communication_history, title, description
        )
        risk_score += comm_risk
        risk_factors.extend([("communication", f) for f in comm_factors])
        risk_details.extend(comm_factors)
        mitigation_suggestions.extend(cm for cm in comm_mitigations if cm not in mitigation_suggestions)

        # Ensure risk score stays within bounds
        risk_score = max(0, min(100, risk_score))

        # Determine risk level
        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "moderate"
        elif risk_score >= 20:
            risk_level = "low"
        else:
            risk_level = "very_low"

        # Generate insights
        insights = self._generate_risk_insights(risk_score, risk_factors, risk_details)

        # Compile final mitigation suggestions (remove duplicates and limit)
        unique_mitigations = list(dict.fromkeys(mitigation_suggestions))  # Preserves order, removes dups

        return {
            "agent": self.agent_name,
            "risk_score": round(risk_score, 1),  # Higher = riskier
            "risk_level": risk_level,
            "risk_factors": [rf[1] for rf in risk_factors],  # Just the descriptions
            "risk_details": risk_details,
            "mitigation_suggestions": unique_mitigations[:8],  # Top 8 unique suggestions
            "risk_breakdown": {
                "price_anomaly": sum(score for factor, score in risk_factors if factor == "price_anomaly"),
                "seller_behavior": sum(score for factor, score in risk_factors if factor == "seller_behavior"),
                "item_condition": sum(score for factor, score in risk_factors if factor == "item_condition"),
                "transaction_details": sum(score for factor, score in risk_factors if factor == "transaction_details"),
                "external_factors": sum(score for factor, score in risk_factors if factor == "external_factors"),
                "documentation": sum(score for factor, score in risk_factors if factor == "documentation"),
                "category_risk": sum(score for factor, score in risk_factors if factor == "category_risk"),
                "timing": sum(score for factor, score in risk_factors if factor == "timing"),
                "communication": sum(score for factor, score in risk_factors if factor == "communication")
            },
            "confidence": 0.85,  # Confidence based on internal data quality
            "recommended_action": self._get_recommended_action(risk_level)
        }

    def _assess_price_anomaly_risk_internal(self, price: Optional[float],
                                          title: str, description: str,
                                          opportunity_data: dict) -> tuple:
        """Assess risk from pricing anomalies using internal logic."""
        risk_score = 0
        factors = []
        mitigations = []

        if price is None or price <= 0:
            factors.append("No price specified - unable to assess pricing risk")
            mitigations.append("Request clear pricing information")
            return 15, factors, mitigations  # Moderate risk for missing price

        text_to_check = f"{title} {description}".lower()

        # Check for too-good-to-be-true pricing
        if price < 20:
            risk_score += 20
            factors.append("Extremely low price (<$20) - high scam potential")
            mitigations.append("Exercise extreme caution - likely scam or stolen goods")
        elif price < 50:
            risk_score += 10
            factors.append("Very low price (<$50) - increased scam risk")
            mitigations.append("Verify authenticity and insist on safe transaction method")

        # Internal market value estimation based on category, brand, condition
        estimated_market_value = self._estimate_internal_market_value(
            opportunity_data.get("category", ""),
            opportunity_data.get("brand", ""),
            opportunity_data.get("condition", ""),
            opportunity_data.get("year"),
            opportunity_data.get("title", ""),
            opportunity_data.get("description", "")
        )

        if estimated_market_value and estimated_market_value > 0:
            ratio = price / estimated_market_value
            if ratio < 0.3:
                risk_score += 25
                factors.append(f"Price (${price}) is <30% of estimated market value (${estimated_market_value:.2f}) - likely scam/stolen")
                mitigations.append("Do not proceed - almost certainly fraudulent or stolen property")
            elif ratio < 0.5:
                risk_score += 15
                factors.append(f"Price (${price}) is <50% of estimated market value (${estimated_market_value:.2f}) - significant discount")
                mitigations.append("Extreme caution warranted - verify authenticity thoroughly")
            elif ratio < 0.7:
                risk_score += 5
                factors.append(f"Price (${price}) is 50-70% of estimated market value (${estimated_market_value:.2f}) - notable discount")
                mitigations.append("Legitimate but investigate reason for discount")
            elif ratio > 3.0:
                risk_score += 20
                factors.append(f"Price (${price}) is >3x estimated market value (${estimated_market_value:.2f}) - likely overpriced")
                mitigations.append("Research comparable sales - likely inflated asking price")
            elif ratio > 2.0:
                risk_score += 10
                factors.append(f"Price (${price}) is >2x estimated market value (${estimated_market_value:.2f}) - premium pricing")
                mitigations.append("Justify premium with condition, rarity, or inclusions")
        else:
            # If we couldn't estimate market value, note it as a limitation
            factors.append("Unable to estimate market value through internal models")
            mitigations.append("Research comparable sales independently to assess pricing")

        # Check for pricing language that indicates urgency or pressure
        pressure_indicators = [
            "priced to sell", "must sell", "below market", "way below market",
            "fire sale", "blowout", "clearance", "everything must go"
        ]
        for indicator in pressure_indicators:
            if indicator in text_to_check:
                risk_score += 5
                factors.append(f"Pricing language indicates urgency: '{indicator}'")
                # Mitigation already covered in general advice
                break

        return risk_score, factors, mitigations

    def _estimate_internal_market_value(self, category: str, brand: str, condition: str,
                                      year: Optional[int], title: str, description: str) -> Optional[float]:
        """Estimate market value using internal models and data."""
        # Base values by category (in USD)
        base_values = {
            "electronics": 100,
            "phones": 200,
            "computers": 300,
            "laptops": 250,
            "tablets": 150,
            "video_games": 50,
            "consoles": 200,
            "tv": 300,
            "audio": 150,
            "cameras": 250,
            "appliances": 200,
            "furniture": 150,
            "home_decor": 50,
            "tools": 75,
            "outdoor": 100,
            "sports": 75,
            "bicycles": 200,
            "fitness": 100,
            "watches": 150,
            "jewelry": 100,
            "handbags": 80,
            "shoes": 60,
            "clothing": 25,
            "toys": 20,
            "books": 10,
            "video_games": 20,
            "collectibles": 50,
            "art": 100,
            "musical_instruments": 150,
            "vehicles": 5000,
            "cars": 8000,
            "trucks": 10000,
            "motorcycles": 3000,
            "rv": 15000,
            "boats": 5000,
            "real_estate": 100000,
            "land": 50000
        }

        # Get base value
        base_value = 50  # Default
        for cat_key, base_val in base_values.items():
            if cat_key in category or category in cat_key:
                base_value = base_val
                break

        # Apply brand multiplier
        brand_multiplier = 1.0
        luxury_brands = ["rolex", "omega", "patek", "audemars", "gucci", "louis vuitton",
                        "chanel", "hermes", "prada", "burberry", "dior", "versace",
                        "apple", "sony", "samsung", "canon", "nikon", "bose", "louis vuitton"]
        premium_brands = ["bose", "sony", "samsung", "apple", "lg", "panasonic", "canon", "nikon",
                         "toyota", "honda", "ford", "bmw", "mercedes", "audi", "lexus"]
        budget_brands = ["walmart", "target", "kdollar", "dollartree", "alibaba", "wish"]

        brand_lower = brand.lower()
        if any(luxury in brand_lower for luxury in luxury_brands):
            brand_multiplier = 3.0
        elif any(premium in brand_lower for premium in premium_brands):
            brand_multiplier = 1.5
        elif any(budget in brand_lower for budget in budget_brands):
            brand_multiplier = 0.5

        # Apply condition multiplier
        condition_multiplier = 1.0
        if "new" in condition or "like new" in condition or "excellent" in condition:
            condition_multiplier = 1.0
        elif "good" in condition:
            condition_multiplier = 0.7
        elif "fair" in condition:
            condition_multiplier = 0.4
        elif "poor" in condition or "broken" in condition or "damaged" in condition:
            condition_multiplier = 0.1
        elif "for parts" in condition or "not working" in condition:
            condition_multiplier = 0.05

        # Apply age/depreciation factor (if year is provided)
        age_factor = 1.0
        if year and year > 0:
            current_year = datetime.now().year
            age = current_year - year
            if age > 0:
                # Different depreciation rates by category
                depreciation_rates = {
                    "electronics": 0.25,  # 25% per year
                    "phones": 0.30,
                    "computers": 0.25,
                    "laptops": 0.25,
                    "tablets": 0.20,
                    "video_games": 0.15,
                    "consoles": 0.15,
                    "tv": 0.15,
                    "audio": 0.10,
                    "cameras": 0.10,
                    "appliances": 0.08,
                    "furniture": 0.05,
                    "tools": 0.05,
                    "outdoor": 0.05,
                    "sports": 0.05,
                    "bicycles": 0.10,
                    "fitness": 0.10,
                    "watches": 0.03,  # Watches depreciate slowly
                    "jewelry": 0.02,  # Jewelry holds value well
                    "handbags": 0.05,
                    "shoes": 0.20,
                    "clothing": 0.30,
                    "toys": 0.25,
                    "books": 0.05,
                    "collectibles": -0.05,  # Some collectibles appreciate
                    "art": -0.02,  # Art can appreciate
                    "musical_instruments": 0.03,
                    "vehicles": 0.15,
                    "cars": 0.15,
                    "trucks": 0.15,
                    "motorcycles": 0.18,
                    "rv": 0.10,
                    "boats": 0.08,
                    "real_estate": -0.02,  # Real estate often appreciates
                    "land": -0.01
                }

                depreciation_rate = 0.10  # Default
                for cat_key, rate in depreciation_rates.items():
                    if cat_key in category or category in cat_key:
                        depreciation_rate = rate
                        break

                # Apply depreciation (but not below 10% of original value for most items)
                depreciation = max(0.10, 1.0 - (depreciation_rate * age))
                age_factor = depreciation

        # Calculate final estimated value
        estimated_value = base_value * brand_multiplier * condition_multiplier * age_factor

        # Apply some randomness to simulate market variation (±15%)
        import random
        variation_factor = 0.85 + (random.random() * 0.3)  # 0.85 to 1.15
        estimated_value *= variation_factor

        return max(estimated_value, 1.0)  # Ensure at least $1 value

    def _assess_seller_behavior_risk(self, seller_info: dict, communication_history: list,
                                   price: Optional[float]) -> tuple:
        """Assess risk from seller behavior and history."""
        risk_score = 0
        factors = []
        mitigations = []

        # Check seller identity verification
        if not seller_info:
            factors.append("No seller information provided")
            mitigations.append("Request seller verification details")
            risk_score += 10
        else:
            # Check for verification status
            if not seller_info.get("verified", False) and not seller_info.get("identity_verified", False):
                if seller_info.get("user_id") or seller_info.get("username"):
                    factors.append("Seller identity not verified")
                    mitigations.append("Request identity verification or use platform protection")
                    risk_score += 8
                else:
                    factors.append("No identifiable seller information")
                    mitigations.append("Unable to verify seller - high risk")
                    risk_score += 15

            # Check seller history/feedback
            feedback_score = seller_info.get("feedback_score")
            feedback_count = seller_info.get("feedback_count", 0)
            if feedback_score is not None:
                if feedback_score < 80:  # Assuming percentage or 0-100 scale
                    risk_score += (80 - feedback_score) // 4  # Up to 20 points for poor feedback
                    factors.append(f"Low seller feedback score: {feedback_score}%")
                    mitigations.append("Review negative feedback carefully before proceeding")
                elif feedback_score < 90:
                    risk_score += 5
                    factors.append(f"Moderate seller feedback score: {feedback_score}%")
                    mitigations.append("Consider starting with small transaction if proceeding")

            if feedback_count < 10:
                risk_score += 5
                factors.append(f"Limited seller history: {feedback_count} feedback entries")
                mitigations.append("Prefer sellers with established track record")
            elif feedback_count < 50:
                risk_score += 2
                factors.append(f"Moderate seller history: {feedback_count} feedback entries")

        # Analyze communication patterns if available
        if communication_history:
            urgent_messages = 0
            vague_messages = 0
            reluctant_to_meet = 0

            for msg in communication_history:
                msg_lower = msg.lower() if isinstance(msg, str) else str(msg).lower()
                # Check for urgency/pressure
                if any(phrase in msg_lower for phrase in ["asap", "hurry", "today only", "last chance"]):
                    urgent_messages += 1
                # Check for vagueness/evasiveness
                if any(phrase in msg_lower for phrase in ["i'll tell you later", "details coming", "soon"]):
                    vague_messages += 1
                # Check reluctance for verification
                if any(phrase in msg_lower for phrase in ["no inspections", "as is only", "dont waste my time"]):
                    reluctant_to_meet += 1

            if urgent_messages > len(communication_history) * 0.5:
                risk_score += 10
                factors.append("Frequent pressure tactics in communication")
                mitigations.append("Do not rush - take time to verify despite pressure")
            if vague_messages > len(communication_history) * 0.3:
                risk_score += 8
                factors.append("Evasive or vague responses to questions")
                mitigations.append("Insist on clear answers before proceeding")
            if reluctant_to_meet > 0:
                risk_score += 12
                factors.append("Seller resistant to verification or inspection")
                mitigations.append("Strongly consider walking away - unwilling to verify")

        # If price is very high, check for signs of inflated ego/unrealistic seller
        if price and price > 10000:
            # High-value items attract more scammers
            risk_score += 5
            factors.append("High-value item attracts increased scammer attention")
            mitigations.append("Use escrow service and verify identity thoroughly")

        return risk_score, factors, mitigations

    def _assess_item_condition_risk(self, condition: str, title: str, description: str,
                                  photos_count: int, video_available: bool) -> tuple:
        """Assess risk related to item condition and verifiability."""
        risk_score = 0
        factors = []
        mitigations = []

        text_to_check = f"{title} {description} {condition}".lower()

        # Check for condition obscurity
        vague_condition_terms = ["as is", "where is", "as-is", "where-is", "no returns", "final sale"]
        for term in vague_condition_terms:
            if term in text_to_check:
                risk_score += 10
                factors.append(f"Vague/limiting condition terminology: '{term}'")
                mitigations.append("Insist on detailed condition description and return options")
                break

        # Check for damage indicators without details
        damage_terms = ["damaged", "broken", "not working", "defective", "faulty", "issues", "problems"]
        damage_count = sum(1 for term in damage_terms if term in text_to_check)
        if damage_count >= 2:
            risk_score += 10
            factors.append("Multiple indications of damage/problems without details")
            mitigations.append("Request specific details about all issues and repair estimates")
        elif damage_count == 1:
            risk_score += 5
            factors.append("Some indication of problems - need clarification")
            mitigations.append("Ask for specific details about any noted issues")

        # Check photo/video availability
        if photos_count == 0:
            risk_score += 15
            factors.append("No photos provided - cannot verify condition or existence")
            mitigations.append("Do not proceed without multiple clear photos")
        elif photos_count < 3:
            risk_score += 8
            factors.append(f"Only {photos_count} photo(s) provided - limited visual verification")
            mitigations.append("Request additional photos from all angles and of any flaws")
        else:
            # Good photo count reduces risk
            risk_score -= min(5, photos_count // 3)  # Up to -5 for lots of photos

        if not video_available and photos_count < 5:
            # Video is especially valuable for complex items
            if any(item in text_to_check for item in ["vehicle", "machinery", "equipment", "electronics"]):
                risk_score += 5
                factors.append("No video available for complex item assessment")
                mitigations.append("Request video demonstration of operation/functionality")

        # Check for stock photo indicators
        stock_photo_indicators = ["stock photo", "catalog image", "manufacturer photo", "file photo"]
        if any(indicator in text_to_check for indicator in stock_photo_indicators):
            risk_score += 15
            factors.append("Indicates use of stock/manufacturer photos - may not show actual item")
            mitigations.append("Insist on photos of the actual item being sold")

        # Check for refusal to provide specifics
        if any(phrase in text_to_check for phrase in ["dont ask", "dont waste time", "serious inquiries only"]):
            risk_score += 10
            factors.append("Seller appears unwilling to answer questions")
            mitigations.append("Consider this a red flag - legitimate sellers welcome questions")

        return risk_score, factors, mitigations

    def _assess_transaction_details_risk(self, payment_terms: str, shipping_info: str, location: str) -> tuple:
        """Assess risk from payment and transaction details."""
        risk_score = 0
        factors = []
        mitigations = []

        # Payment method risk
        if payment_terms:
            payment_risk_score = 0
            detected_methods = []
            for method, risk in self.payment_risk.items():
                if method in payment_terms:
                    payment_risk_score += risk
                    detected_methods.append(method)

            if detected_methods:
                risk_score += payment_risk_score
                methods_str = ", ".join(detected_methods)
                factors.append(f"Payment method(s) detected: {methods_str}")

                # Add specific mitigations
                if "wire_transfer" in detected_methods or "money_order" in detected_methods:
                    mitigations.append("Avoid wire transfers/money orders - no recourse if scammed")
                if "gift_card" in detected_methods:
                    mitigations.append("Gift card payments are almost always scams - do not accept")
                if "cryptocurrency" in detected_methods:
                    mitigations.append("Cryptocurrency payments offer minimal fraud protection")
                if "cash" in detected_methods and not location:
                    mitigations.append("Cash transactions require extreme caution and safe meeting practices")
                if "paypal" in detected_methods or "credit_card" in detected_methods:
                    mitigations.append("These methods offer some buyer protection - verify coverage")
                if "escrow" in detected_methods:
                    risk_score -= 10  # Escrow reduces risk
                    factors.append("Escrow service mentioned - reduces transaction risk")
                    mitigations.append("Verify escrow service legitimacy before use")
            else:
                # No recognizable payment method - could be good or bad
                if "paypal" not in payment_terms and "credit card" not in payment_terms:
                    risk_score += 5
                    factors.append("Unclear or unconventional payment terms specified")
                    mitigations.append("Clarify payment methods and ensure buyer protection")

        else:
            # No payment terms specified
            risk_score += 5
            factors.append("No payment terms specified")
            mitigations.append("Clarify acceptable payment methods before proceeding")

        # Shipping/delivery risks
        if shipping_info:
            # Red flags for shipping
            shipping_red_flags = ["buyer pays shipping", "ship to unverified address", "po box only",
                                "international buyer", "ship to freight forwarder", "drop shipping"]
            for flag in shipping_red_flags:
                if flag in shipping_info:
                    risk_score += 10
                    factors.append(f"Shipping concern: '{flag}'")
                    if "po box" in flag or "freight forwarder" in flag:
                        mitigations.append("Avoid shipping to unverified addresses or freight forwarders")
                    elif "international" in flag:
                        mitigations.append("International shipping increases fraud risk and complicates recourse")
                    break

            # Positive shipping indicators
            shipping_positive = ["insured", "tracking", "signature required", "carrier insurance"]
            for positive in shipping_positive:
                if positive in shipping_info:
                    risk_score -= 3
                    factors.append(f"Positive shipping feature: '{positive}'")
                    break
        else:
            # No shipping info - assume local pickup
            if not location:
                risk_score += 5
                factors.append("No location or shipping information provided")
                mitigations.append("Clarify whether item is for local pickup or shipping required")

        # Location-based risks
        if location:
            location_lower = location.lower()
            # High-risk locations for meetings
            high_risk_locations = ["parking lot", "street corner", "alley", "behind building",
                                 "warehouse district", "industrial area"]
            for loc in high_risk_locations:
                if loc in location_lower:
                    risk_score += 12
                    factors.append(f"Suggested meeting location appears high-risk: '{loc}'")
                    mitigations.append("Insist on meeting in well-lit, public place with surveillance")
                    break
            # Safe locations
            safe_locations = ["police station", "bank lobby", "storefront", "coffee shop",
                            "shopping mall", "public library"]
            for loc in safe_locations:
                if loc in location_lower:
                    risk_score -= 5
                    factors.append(f"Suggested meeting location appears safe: '{loc}'")
                    break

            # Remote/rural location risks (harder to verify, limited recourse)
            rural_indicators = ["rural", "remote", "country", "farm", "outback", "wilderness"]
            if any(indicator in location_lower for indicator in rural_indicators):
                risk_score += 5
                factors.append("Remote location may limit verification options and recourse")
                mitigations.append("Consider additional verification steps due to location")
        else:
            # No location at all
            risk_score += 8
            factors.append("No location information provided")
            mitigations.append("Obtain location details before considering transaction")

        return risk_score, factors, mitigations

    def _assess_external_factors_risk_internal(self, category: str, brand: str, listed_date_str: str,
                                              opportunity_data: dict) -> tuple:
        """Assess risk from external factors like market conditions, trends, etc. using internal logic."""
        risk_score = 0
        factors = []
        mitigations = []

        # Category-based risk (checking for counterfeits)
        high_counterfeit_risk = ["watches", "handbags", "sneakers", "jeans", "sunglasses",
                               "makeup", "perfume", "electronics", "software", "video games"]
        if any(item in category for item in high_counterfeit_risk):
            risk_score += 8
            factors.append(f"Category ({category}) has high counterfeit prevalence")
            mitigations.append("Exercise extra vigilance regarding authenticity verification")

        # Brand-specific risks
        if brand:
            high_risk_brands = ["rolex", "omega", "louis vuitton", "gucci", "chanel", "hermes",
                              "supreme", "yeezy", "jordans", "apple", "samsung"]
            if any(b in brand for b in high_risk_brands):
                risk_score += 5
                factors.append(f"Brand ({brand}) frequently targeted by counterfeiters")
                mitigations.append("Verify authenticity through authorized channels if possible")

        # Timing-based risks (scams often increase during certain periods)
        if listed_date_str:
            try:
                if isinstance(listed_date_str, str):
                    listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_date_str

                # Check if listed during high-risk periods
                month = listed_date.month
                day = listed_date.day

                # Holiday seasons (Nov-Jan) see increased scam activity
                if month in [11, 12, 1]:
                    risk_score += 3
                    factors.append("Listed during holiday season - heightened scam awareness advised")
                    mitigations.append("Extra vigilance recommended during holiday shopping season")

                # Tax season (Feb-Apr) - increased financial stress scams
                if month in [2, 3, 4]:
                    risk_score += 2
                    factors.append("Listed during tax season - be aware of financially motivated scams")

                # End of month (financial pressure)
                if day >= 25:
                    risk_score += 1
                    factors.append("Listed late in month - potential financial pressure motivation")

            except Exception:
                pass  # Ignore date parsing errors for risk assessment

        # General market volatility assessment based on category
        volatile_categories = ["cryptocurrency", "stocks", "collectibles", "art", "jewelry", "precious metals"]
        if any(vol_cat in category for vol_cat in volatile_categories):
            risk_score += 5
            factors.append(f"Category ({category}) known for price volatility")
            mitigations.append("Be aware that market values can fluctuate significantly")

        return risk_score, factors, mitigations

    def _assess_documentation_risk(self, opportunity_data: dict) -> tuple:
        """Assess risk from missing or inadequate documentation."""
        risk_score = 0
        factors = []
        mitigations = []

        # Check for availability of key documents
        has_title = opportunity_data.get("title_document", False) or "title" in str(opportunity_data.get("description", "")).lower()
        has_registration = opportunity_data.get("registration", False) or "registration" in str(opportunity_data.get("description", "")).lower()
        has_service_records = opportunity_data.get("service_records", False) or "service" in str(opportunity_data.get("description", "")).lower()
        has_receipt = opportunity_data.get("original_receipt", False) or "receipt" in str(opportunity_data.get("description", "")).lower()
        has_warranty = opportunity_data.get("warranty_info", False) or "warranty" in str(opportunity_data.get("description", "")).lower()
        has_manual = opportunity_data.get("manual", False) or "manual" in str(opportunity_data.get("description", "")).lower()

        # Vehicle-specific documentation
        if any(v in str(opportunity_data.get("category", "")).lower() for v in ["vehicle", "car", "truck", "motorcycle", "boat", "rv"]):
            if not has_title:
                risk_score += 20
                factors.append("No title mentioned for vehicle - major legal risk")
                mitigations.append("Do not purchase vehicle without clear title")
            if not has_registration:
                risk_score += 10
                factors.append("No current registration mentioned")
                mitigations.append("Verify registration status and transfer process")
            if not has_service_records:
                risk_score += 5
                factors.append("No service history mentioned")
                mitigations.append("Request service records or prepare for potential hidden issues")

        # Electronics/appliance documentation
        elif any(e in str(opportunity_data.get("category", "")).lower() for e in ["electronics", "computer", "phone", "appliance"]):
            if not has_manual:
                risk_score += 3
                factors.append("No manual mentioned")
                mitigations.append("Manual may be available online from manufacturer")
            if not has_warranty:
                # Not necessarily a risk, but worth noting
                pass
            if "as is" in str(opportunity_data.get("description", "")).lower() and not has_original_receipt:
                risk_score += 8
                factors.append("As-is electronics without proof of purchase - limited recourse")
                mitigations.append("Consider that you may have no warranty or return options")

        # High-value items (>$1000) without documentation
        price = opportunity_data.get("price")
        if price and price > 1000:
            docs_mentioned = sum([has_title, has_registration, has_service_records,
                                has_receipt, has_warranty, has_manual])
            if docs_mentioned == 0:
                risk_score += 12
                factors.append("High-value item (>$1000) with no documentation mentioned")
                mitigations.append("Insist on documentation for high-value purchases")
            elif docs_mentioned <= 1:
                risk_score += 6
                factors.append("High-value item with minimal documentation mentioned")
                mitigations.append("Consider what documentation would be reasonable to expect")

        # General lack of documentation
        if not any([has_title, has_registration, has_service_records, has_receipt, has_warranty, has_manual]):
            if not any(cat in str(opportunity_data.get("category", "")).lower()
                    for cat in ["vehicle", "equipment", "machinery"]):
                # For non-vehicle/equipment items, some flexibility
                if price and price > 100:
                    risk_score += 5
                    factors.append("Limited documentation for item over $100")
                    mitigations.append("Consider what verification methods are available")

        return risk_score, factors, mitigations

    def _assess_category_risk(self, category: str) -> int:
        """Assess base risk level by category."""
        # Check high-risk categories first
        for cat_key, risk_value in self.high_risk_categories.items():
            if cat_key in category or category in cat_key:
                return risk_value

        # Check low-risk categories
        for cat_key, risk_reduction in self.low_risk_categories.items():
            if cat_key in category or category in cat_key:
                return risk_reduction

        # Default moderate risk
        return 0

    def _assess_timing_risk(self, listed_date_str: str) -> tuple:
        """Assess risk based on listing timing and duration."""
        risk_score = 0
        factors = []
        mitigations = []

        if not listed_date_str:
            return risk_score, factors, mitigations

        try:
            if isinstance(listed_date_str, str):
                listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
            else:
                listed_date = listed_date_str

            days_listed = (datetime.now() - listed_date.replace(tzinfo=None)).days

            # Very new listings can be riskier (scammers post and vanish quickly)
            if days_listed < 1:
                risk_score += 8
                factors.append("Just listed - scammers often post fresh listings")
                mitigations.append("Exercise extra caution with brand new listings")
            elif days_listed < 3:
                risk_score += 4
                factors.append("Recently listed - verify seller consistency over time")

            # Very old listings may indicate problems
            elif days_listed > 90:
                risk_score += 10
                factors.append("Listed for over 3 months - may indicate issues")
                mitigations.append("Investigate why item hasn't sold - may have hidden problems")
            elif days_listed > 60:
                risk_score += 5
                factors.append("Listed for over 2 months - consider reason for prolonged listing")
                mitigations.append("Ask if price has been reduced or if there are known issues")

            # Seasonal timing considerations
            month = listed_date.month
            # Post-holiday returns/scams (Jan-Feb)
            if month in [1, 2]:
                risk_score += 3
                factors.append("Listed post-holiday season - watch for return fraud or gifted items")
                mitigations.append("Verify item wasn't received as gift or stolen during holidays")

            # Summer vacation scams (Jun-Aug)
            if month in [6, 7, 8]:
                risk_score += 2
                factors.append("Listed during summer vacation season - increased travel-related scams")
                mitigations.append("Be wary of sellers claiming to be deployed/vacationing")

        except Exception:
            # If we can't parse date, minimal risk impact
            pass

        return risk_score, factors, mitigations

    def _assess_communication_risk(self, communication_history: list, title: str, description: str) -> tuple:
        """Assess risk from communication patterns and content."""
        risk_score = 0
        factors = []
        mitigations = []

        if not communication_history:
            # No communication history to analyze
            return risk_score, factors, mitigations

        # Combine all communications for analysis
        all_comm = " ".join([str(msg).lower() for msg in communication_history])

        # Check for red flag phrases
        red_flag_count = 0
        found_flags = []
        for flag in self.communication_red_flags:
            if flag in all_comm:
                red_flag_count += 1
                found_flags.append(flag)

        if red_flag_count >= 3:
            risk_score += 15
            factors.append(f"Multiple communication red flags detected: {', '.join(found_flags[:3])}...")
            mitigations.append("Multiple pressure tactics or inconsistencies - proceed with extreme caution")
        elif red_flag_count >= 2:
            risk_score += 10
            factors.append(f"Communication red flags: {', '.join(found_flags)}")
            mitigations.append("Noticeable concerning patterns in communication - verify thoroughly")
        elif red_flag_count >= 1:
            risk_score += 5
            factors.append(f"Communication red flag: '{found_flags[0]}'")
            # Individual flags handled by general advice

        # Check for inconsistency in stories/details
        # This is simplified - real implementation would use NLP
        inconsistency_indicators = [
            "actually", "i meant", "let me clarify", "what i really meant is",
            "to be clear", "when i said", "i should have said"
        ]
        inconsistency_count = sum(1 for indicator in inconsistency_indicators if indicator in all_comm)
        if inconsistency_count >= 3:
            risk_score += 8
            factors.append("Multiple indications of inconsistent or changing descriptions")
            mitigations.append("Note inconsistencies and seek clarification on all points")

        # Check for excessive flattery or manipulation tactics
        manipulation_indicators = [
            "you seem like", "i trust you", "you're honest", "good person",
            "deserves a good home", "someone who will appreciate it",
            "i've had it my whole life", "sentimental value"
        ]
        manipulation_count = sum(1 for indicator in manipulation_indicators if indicator in all_comm)
        if manipulation_count >= 2:
            risk_score += 6
            factors.append("Possible emotional manipulation tactics detected")
            mitigations.append("Stay objective - don't let sentiment override due diligence")

        # Check for avoidance of platform protection
        avoidance_phrases = [
            "let's do this off-platform", "avoid fees", "save the fees",
            "direct deal better", "wire to avoid paypal fees",
            "meet in person to avoid platform"
        ]
        avoidance_count = sum(1 for phrase in avoidance_phrases if phrase in all_comm)
        if avoidance_count >= 1:
            risk_score += 12
            factors.append("Attempt to avoid platform protection detected")
            mitigations.append("STRONGLY ADVISED: Keep transaction on platform for protection")
            # This is a major red flag - additional emphasis below
            if len(communication_history) > 2:
                risk_score += 8  # Extra weight if repeated

        return risk_score, factors, mitigations

    def _generate_risk_insights(self, risk_score: float, risk_factors: list, risk_details: list) -> list:
        """Generate insights from the risk analysis."""
        insights = []

        # Overall risk assessment
        if risk_score >= 80:
            insights.append("CRITICAL RISK: Multiple serious concerns indicate likely fraud or major problems")
        elif risk_score >= 60:
            insights.append("HIGH RISK: Significant risk factors warrant extreme caution or avoidance")
        elif risk_score >= 40:
            insights.append("MODERATE RISK: Several concerns require careful verification and mitigation")
        elif risk_score >= 20:
            insights.append("LOW RISK: Minor concerns manageable with standard precautions")
        else:
            insights.append("VERY LOW RISK: Minimal identifiable risks with standard safeguards")

        # Category-specific insights
        high_risk_factors = [desc for factor, desc in risk_factors if factor in ["category_risk", "external_factors"]
                           and ("high-risk" in desc.lower() or "counterfeit" in desc.lower())]
        if high_risk_factors:
            insights.append("Item belongs to category with elevated fraud/counterfeit concerns")

        # Communication insights
        comm_risk_factors = [desc for factor, desc in risk_factors if factor == "communication"]
        if any("avoid platform" in desc.lower() for desc in comm_risk_factors):
            insights.append("Attempt to circumvent platform protections detected - major red flag")
        if any("pressure" in desc.lower() or "urgency" in desc.lower() for desc in comm_risk_factors):
            insights.append("High-pressure sales tactics suggest potential scam")

        # Documentation insights
        doc_risk_factors = [desc for factor, desc in risk_factors if factor == "documentation"]
        if any("no title" in desc.lower() for desc in doc_risk_factors):
            insights.append("Missing title documentation presents significant legal/financial risk")
        if any("high-value item" in desc.lower() and "no documentation" in desc.lower() for desc in doc_risk_factors):
            insights.append("High-value item lacks expected documentation - increases risk substantially")

        return insights[:4]  # Limit to top 4 insights

    def _get_recommended_action(self, risk_level: str) -> str:
        """Get recommended action based on risk level."""
        action_map = {
            "critical": "AVOID - Strong evidence of fraud or serious issues",
            "high": "AVOID or EXTREME CAUTION - Significant risks require extraordinary verification",
            "moderate": "PROCEED WITH CAUTION - Verify all claims and use protective measures",
            "low": "PROCEED WITH STANDARD PRECAUTIONS - Normal due diligence advised",
            "very_low": "PROCEED WITH CONFIDENCE - Minimal risks identified"
        }
        return action_map.get(risk_level, "PROCEED WITH CAUTION - Unknown risk level")