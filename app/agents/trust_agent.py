"""Trust Agent: assesses source reliability, seller reputation, data integrity."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from datetime import datetime
import hashlib
import math

logger = logging.getLogger(__name__)


class TrustAgent(BaseAgent):
    """Agent responsible for evaluating trust signals and source credibility."""

    def __init__(self):
        super().__init__("TrustAgent")
        # Known trusted sources (in production, this would come from a database/API)
        self.trusted_sources = {
            "certified dealer": 0.9,
            "manufacturer": 0.95,
            "authorized reseller": 0.85,
            "official store": 0.9,
            "reputable marketplace": 0.75,
            "established broker": 0.8
        }

        # Known risky sources
        self.risky_sources = {
            "unknown": 0.2,
            "private seller": 0.4,
            "auction": 0.5,
            "individual": 0.35,
            "unverified dealer": 0.3
        }

        # Certificate authorities we trust (simplified)
        self.trusted_cas = [
            "DigiCert", "Let's Encrypt", "Comodo", "Sectigo", "GoDaddy",
            "GlobalSign", "Amazon", "Microsoft", "Google", "Apple",
            "Thawte", "RapidSSL", "GeoTrust", "Network Solutions"
        ]

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assess trustworthiness of the opportunity source and data.

        Returns trust score, risk flags, and recommendations.
        """
        self._log_info("Processing trust analysis")

        # Initialize scores and flags
        trust_score = 50  # Start with neutral score
        risk_flags = []
        trust_components = {
            "source_verification": 0,
            "data_consistency": 0,
            "actor_verification": 0,
            "signal_forensics": 0
        }
        notes = []

        # 1. Source Verification
        source_score, source_flags, source_notes = await self._verify_source(opportunity_data)
        trust_score += source_score
        trust_components["source_verification"] = source_score
        risk_flags.extend(source_flags)
        notes.extend(source_notes)

        # 2. Data Consistency Check
        consistency_score, consistency_flags, consistency_notes = await self._check_data_consistency(opportunity_data)
        trust_score += consistency_score
        trust_components["data_consistency"] = consistency_score
        risk_flags.extend(consistency_flags)
        notes.extend(consistency_notes)

        # 3. Actor Verification (Seller/Broker)
        actor_score, actor_flags, actor_notes = await self._verify_actor(opportunity_data, context)
        trust_score += actor_score
        trust_components["actor_verification"] = actor_score
        risk_flags.extend(actor_flags)
        notes.extend(actor_notes)

        # 4. Signal Forensics (Document verification, review authenticity)
        signal_score, signal_flags, signal_notes = await self._analyze_signals(opportunity_data)
        trust_score += signal_score
        trust_components["signal_forensics"] = signal_score
        risk_flags.extend(signal_flags)
        notes.extend(signal_notes)

        # Ensure score stays within bounds
        trust_score = max(0, min(100, trust_score))

        # Determine risk level based on final score
        risk_level = "low"
        if trust_score < 30:
            risk_level = "critical"
        elif trust_score < 45:
            risk_level = "high"
        elif trust_score < 60:
            risk_level = "medium"
        elif trust_score < 80:
            risk_level = "low"
        else:
            risk_level = "very_low"

        # Generate recommendations based on findings
        recommendations = self._generate_trust_recommendations(trust_score, risk_flags, trust_components)

        return {
            "agent": self.agent_name,
            "trust_score": round(trust_score, 1),
            "risk_level": risk_level,
            "risk_factors": list(set(risk_flags)),  # Remove duplicates
            "trust_components": trust_components,
            "notes": "; ".join(notes) if notes else "Trust analysis completed",
            "confidence": 0.85,  # High confidence in this analysis
            "suggested_actions": recommendations
        }

    async def _verify_source(self, opportunity_data: dict) -> tuple:
        """Verify the source of the opportunity (website, platform, etc.).

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        source = opportunity_data.get("source", "").lower().strip()
        if not source:
            source = opportunity_data.get("platform", "").lower().strip()

        url = opportunity_data.get("url", "").lower()

        if source:
            # Check against known trusted sources
            found_trusted = False
            for trusted_source, trust_value in self.trusted_sources.items():
                if trusted_source in source:
                    score_adj += int((trust_value - 0.5) * 50)  # Convert to -25 to +25 range
                    flags.append(f"trusted_source:{trusted_source}")
                    notes.append(f"Source '{source}' matches trusted source '{trusted_source}'")
                    found_trusted = True
                    break

            if not found_trusted:
                # Check against known risky sources
                for risky_source, risk_value in self.risky_sources.items():
                    if risky_source in source:
                        score_adj += int((risk_value - 0.5) * 50)  # Convert to -25 to +25 range
                        flags.append(f"risky_source:{risky_source}")
                        notes.append(f"Source '{source}' matches risky source '{risky_source}'")
                        break
                else:
                    # Unknown source - slight penalty
                    score_adj -= 10
                    flags.append("unknown_source")
                    notes.append(f"Source '{source}' is not in known trusted or risky lists")

        # Check URL characteristics
        if url:
            # Check for HTTPS
            if url.startswith("https://"):
                score_adj += 5
                flags.append("https_used")
                notes.append("Website uses HTTPS encryption")
            elif url.startswith("http://"):
                score_adj -= 10
                flags.append("http_only")
                notes.append("Website uses HTTP only (no encryption)")

            # Check for suspicious TLDs
            suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".work", ".xyz", ".top"]
            if any(url.endswith(tld) for tld in suspicious_tlds):
                score_adj -= 15
                flags.append("suspicious_tld")
                notes.append("Website uses a top-level domain often associated with spam/scam sites")

            # Check for IP address instead of domain
            import re
            ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
            if re.search(ip_pattern, url):
                score_adj -= 10
                flags.append("ip_address_url")
                notes.append("Website URL uses IP address instead of domain name")

        # SSL certificate check (simulated)
        if url and url.startswith(("http://", "https://")):
            ssl_score, ssl_flags, ssl_notes = self._simulate_ssl_check(url)
            score_adj += ssl_score
            flags.extend(ssl_flags)
            notes.extend(ssl_notes)

        return score_adj, flags, notes

    def _simulate_ssl_check(self, url: str) -> tuple:
        """Simulate SSL certificate validation without external service."""
        score_adj = 0
        flags = []
        notes = []

        if not url:
            return 0, [], []

        # Extract domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        # In a real implementation, we would check the actual SSL certificate
        # For simulation, we'll use heuristics based on the domain

        # Check if it's a known trusted domain pattern
        trusted_domains = [
            "ebay.com", "amazon.com", "walmart.com", "etsy.com", " craigslist.org",
            "facebook.com", "instagram.com", "linkedin.com", "paypal.com",
            "bankofamerica.com", "chase.com", "wellsfargo.com", "citi.com",
            "gov.uk", "gov.au", "usa.gov", "gov.ca"
        ]

        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            base_domain = f"{domain_parts[-2]}.{domain_parts[-1]}"
            if any(trusted in domain for trusted in trusted_domains):
                score_adj += 10
                flags.append("ssl_trusted_domain")
                notes.append(f"SSL certificate likely from trusted authority for {domain}")
            elif any(suspicious in domain for suspicious in ["bit.ly", "tinyurl", "t.co", "goo.gl"]):
                score_adj -= 20
                flags.append("url_shortener")
                notes.append("URL uses shortening service which can mask malicious destinations")
            else:
                # Default assumption for unknown domains
                score_adj += 0
                flags.append("ssl_unknown")
                notes.append("SSL certificate status unknown for this domain")
        else:
            score_adj -= 5
            flags.append("ssl_check_failed")
            notes.append("Could not perform SSL check")

        return score_adj, flags, notes

    async def _check_data_consistency(self, opportunity_data: dict) -> tuple:
        """Check consistency of data across multiple fields.

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        # Check price consistency with estimated market value (using internal estimation)
        price = opportunity_data.get("price")
        estimated_market_value = self._estimate_market_value_internal(opportunity_data)

        if price is not None and estimated_market_value is not None and estimated_market_value > 0:
            ratio = price / estimated_market_value
            if ratio > 2.5:  # Price is more than 2.5x estimated market value
                score_adj -= 20
                flags.append("price_market_discrepancy_high")
                notes.append(f"Price ({price}) is significantly higher than estimated market value ({estimated_market_value:.0f})")
            elif ratio < 0.4:  # Price is less than 40% of estimated market value
                score_adj -= 15
                flags.append("price_market_discrepancy_low")
                notes.append(f"Price ({price}) is unusually low compared to estimated market value ({estimated_market_value:.0f})")
            elif 0.8 <= ratio <= 1.2:  # Price is close to estimated market value
                score_adj += 10
                flags.append("price_market_consistent")
                notes.append(f"Price ({price}) is consistent with estimated market value ({estimated_market_value:.0f})")
            elif 0.6 <= ratio < 0.8 or 1.2 < ratio <= 1.5:  # Moderate discrepancy
                score_adj -= 5
                flags.append("price_market_moderate_discrepancy")
                notes.append(f"Price ({price}) shows moderate deviation from estimated market value ({estimated_market_value:.0f})")

        # Check description completeness
        description = opportunity_data.get("description", "")
        if len(description) < 30:
            score_adj -= 15
            flags.append("very_short_description")
            notes.append("Opportunity description is very brief (less than 30 characters)")
        elif len(description) < 100:
            score_adj -= 5
            flags.append("short_description")
            notes.append("Opportunity description is relatively short")
        elif len(description) > 500:
            score_adj += 5
            flags.append("detailed_description")
            notes.append("Opportunity description is comprehensive")
        elif len(description) > 200:
            score_adj += 3
            flags.append("good_description_length")
            notes.append("Opportunity description has adequate detail")

        # Check for contradictory information
        title = opportunity_data.get("title", "").lower()
        description_lower = description.lower()

        # Condition contradictions
        condition_indicators_new = ["new", "brand new", "never used", "sealed", "unused"]
        condition_indicators_used = ["used", "pre-owned", "second hand", "previously owned"]

        has_new_indicator = any(indicator in title or indicator in description_lower for indicator in condition_indicators_new)
        has_used_indicator = any(indicator in title or indicator in description_lower for indicator in condition_indicators_used)

        if has_new_indicator and has_used_indicator:
            score_adj -= 15
            flags.append("condition_contradiction")
            notes.append("Title/description contains conflicting condition indicators (new vs used)")

        # Price vs condition contradictions
        if has_new_indicator and price is not None and price < 50:
            # New item priced very low might be suspicious
            score_adj -= 10
            flags.append("new_item_low_price")
            notes.append("Item described as new but priced unusually low")
        elif has_used_indicator and price is not None and price > 1000:
            # Used item priced very high
            # This could be legitimate (luxury goods) so we don't penalize as much
            pass

        # Check for unrealistic claims
        exaggeration_terms = ["best ever", "unbelievable", "amazing deal", "once in a lifetime",
                             "limited time", "act now", "don't miss out", "guaranteed"]
        exaggeration_count = sum(1 for term in exaggeration_terms if term in description_lower)
        if exaggeration_count >= 3:
            score_adj -= 10
            flags.append("exaggerated_language")
            notes.append("Description contains multiple exaggerated marketing claims")

        # Check for contact information consistency
        contact_email = opportunity_data.get("contact_email", "")
        contact_phone = opportunity_data.get("contact_phone", "")
        if contact_email and "@" not in contact_email:
            score_adj -= 10
            flags.append("invalid_email_format")
            notes.append("Contact email appears to be incorrectly formatted")

        if contact_phone:
            # Simple phone validation - should have enough digits
            digits_only = re.sub(r'\D', '', contact_phone)
            if len(digits_only) < 7:
                score_adj -= 5
                flags.append("suspicious_phone_number")
                notes.append("Contact phone number appears too short")

        return score_adj, flags, notes

    def _estimate_market_value_internal(self, opportunity_data: dict) -> Optional[float]:
        """Estimate market value using internal heuristics and databases.

        This replaces the external phia market-value call with internal logic.
        """
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
                "lg": 1.2,
                "bose": 1.8,
                "jbl": 1.3,
                "nike": 1.7,
                "adidas": 1.5,
                "louis vuitton": 5.0,
                "gucci": 4.5,
                "rolex": 10.0,
                "omega": 6.0,
                "cartier": 8.0,
                "ford": 1.2,
                "toyota": 1.3,
                "honda": 1.25,
                "bmw": 2.0,
                "mercedes": 2.2,
                "audi": 1.9
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
            estimated_value = base_value * brand_multiplier * condition_multiplier * age_factor

            # Apply some randomness to simulate market variation (±15%)
            import random
            variation_factor = 0.85 + (random.random() * 0.3)  # 0.85 to 1.15
            estimated_value *= variation_factor

            return max(1.0, estimated_value)  # Minimum $1

        except Exception as e:
            self._log_debug(f"Error in internal market value estimation: {e}")
            return None

    async def _verify_actor(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> tuple:
        """Verify the actor/seller behind the opportunity.

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        seller_id = opportunity_data.get("seller_id")
        seller_name = opportunity_data.get("seller_name", "")
        seller_rating = opportunity_data.get("seller_rating")
        transaction_count = opportunity_data.get("transaction_count", 0)
        feedback_count = opportunity_data.get("feedback_count", 0)
        response_time = opportunity_data.get("response_time_hours")

        # Seller ID verification
        if seller_id:
            if isinstance(seller_id, str):
                if seller_id.startswith("VERIFIED_") or "verified" in seller_id.lower():
                    score_adj += 15
                    flags.append("verified_identity")
                    notes.append("Seller identity verified through platform verification")
                elif seller_id.startswith("ANON_") or "anonymous" in seller_id.lower() or "private" in seller_id.lower():
                    score_adj -= 12
                    flags.append("anonymous_seller")
                    notes.append("Seller identity is anonymous or private")
                elif len(seller_id) < 5:
                    score_adj -= 5
                    flags.append("short_seller_id")
                    notes.append("Seller ID appears unusually short or generic")

        # Seller rating analysis
        if seller_rating is not None:
            try:
                rating_float = float(seller_rating)
                if rating_float >= 4.8:
                    score_adj += 12
                    flags.append("excellent_seller_rating")
                    notes.append(f"Seller has excellent rating: {rating_float}/5")
                elif rating_float >= 4.5:
                    score_adj += 10
                    flags.append("high_seller_rating")
                    notes.append(f"Seller has high rating: {rating_float}/5")
                elif rating_float >= 4.0:
                    score_adj += 7
                    flags.append("good_seller_rating")
                    notes.append(f"Seller has good rating: {rating_float}/5")
                elif rating_float >= 3.5:
                    score_adj += 4
                    flags.append("fair_seller_rating")
                    notes.append(f"Seller has fair rating: {rating_float}/5")
                elif rating_float >= 3.0:
                    score_adj += 0
                    flags.append("mediocre_seller_rating")
                    notes.append(f"Seller has mediocre rating: {rating_float}/5")
                elif rating_float >= 2.0:
                    rating_float = float(seller_rating)
                    if rating_float >= 4.8:
                        score_adj += 12
                        flags.append("excellent_seller_rating")
                        notes.append(f"Seller has excellent rating: {rating_float}/5")
                    elif rating_float >= 4.5:
                        score_adj += 10
                        flags.append("high_seller_rating")
                        notes.append(f"Seller has high rating: {rating_float}/5")
                    elif rating_float >= 4.0:
                        score_adj += 7
                        flags.append("good_seller_rating")
                        notes.append(f"Seller has good rating: {rating_float}/5")
                    elif rating_float >= 3.5:
                        score_adj += 4
                        flags.append("fair_seller_rating")
                        notes.append(f"Seller has fair rating: {rating_float}/5")
                    elif rating_float >= 3.0:
                        score_adj += 0
                        flags.append("mediocre_seller_rating")
                        notes.append(f"Seller has mediocre rating: {rating_float}/5")
                    elif rating_float >= 2.0:
                        score_adj -= 5
                        flags.append("poor_seller_rating")
                        notes.append(f"Seller has poor rating: {rating_float}/5")
                    else:
                        score_adj -= 12
                        flags.append("very_poor_seller_rating")
                        notes.append(f"Seller has very poor rating: {rating_float}/5")
            except (ValueError, TypeError):
                # If rating isn't a valid number, ignore it
                pass

        # Transaction history
        if transaction_count > 0:
            if transaction_count >= 500:
                score_adj += 15
                flags.append("high_volume_seller")
                notes.append(f"Seller has high transaction volume: {transaction_count} completed transactions")
            elif transaction_count >= 100:
                score_adj += 12
                flags.append("established_seller")
                notes.append(f"Seller is well-established: {transaction_count} completed transactions")
            elif transaction_count >= 25:
                score_adj += 8
                flags.append("experienced_seller")
                notes.append(f"Seller has good experience: {transaction_count} completed transactions")
            elif transaction_count >= 5:
                score_adj += 3
                flags.append("some_experience")
                notes.append(f"Seller has some transaction history: {transaction_count} completed transactions")
            else:  # 1-4 transactions
                score_adj -= 5
                flags.append("limited_transaction_history")
                notes.append(f"Seller has limited transaction history: {transaction_count} transactions")
        else:
            score_adj -= 10
            flags.append("no_transaction_history")
            notes.append("Seller has no transaction history on this platform")

        # Feedback count (often correlates with trust)
        if feedback_count > 0:
            if feedback_count >= 1000:
                score_adj += 10
                flags.append("high_feedback_count")
                notes.append(f"Seller has extensive feedback history: {feedback_count} feedback entries")
            elif feedback_count >= 100:
                score_adj += 7
                flags.append("good_feedback_count")
                notes.append(f"Seller has solid feedback history: {feedback_count} feedback entries")
            elif feedback_count >= 20:
                score_adj += 3
                flags.append("some_feedback")
                notes.append(f"Seller has some feedback history: {feedback_count} feedback entries")
            # Less than 20 feedback is neutral or slightly negative depending on other factors

        # Response time (if available)
        if response_time is not None:
            try:
                response_hours = float(response_time)
                if response_hours <= 1:
                    score_adj += 8
                    flags.append("fast_responder")
                    notes.append(f"Seller responds very quickly: {response_hours} hours average")
                elif response_hours <= 6:
                    score_adj += 5
                    flags.append("reasonable_response_time")
                    notes.append(f"Seller has reasonable response time: {response_hours} hours average")
                elif response_hours <= 24:
                    score_adj += 2
                    flags.append("acceptable_response_time")
                    notes.append(f"Seller response time is acceptable: {response_hours} hours average")
                elif response_hours > 72:  # More than 3 days
                    score_adj -= 8
                    flags.append("slow_responder")
                    notes.append(f"Seller is slow to respond: {response_hours} hours average")
                elif response_hours > 24:  # More than 1 day
                    score_adj -= 3
                    flags.append("slowish_responder")
                    notes.append(f"Seller responds somewhat slowly: {response_hours} hours average")
            except (ValueError, TypeError):
                pass

        # Business verification indicators (simulated)
        reg_id = opportunity_data.get("business_registration") or opportunity_data.get("vat_number") or opportunity_data.get("tax_id")
        if reg_id:
            # Simple validation: check if it looks like a real registration number
            if len(str(reg_id)) >= 5 and any(c.isalpha() for c in str(reg_id)):
                score_adj += 8
                flags.append("business_registered")
                notes.append("Seller provides business registration/tax ID information")
            else:
                score_adj += 3
                flags.append("possible_business_id")
                notes.append("Seller provides what might be a business identifier")
        elif opportunity_data.get("is_business_account", False):
            score_adj += 6
            flags.append("business_account")
            notes.append("Seller is marked as a business/commercial account")

        # Check for scam warning signs in seller name/description
        seller_text = f"{seller_name} {opportunity.get('description', '')}".lower()
        scam_indicators = [
            "urgent sale", "must sell quickly", "moving abroad", "deployed military",
            "financial hardship", "divorce settlement", "inheritance", "widow selling",
            "no time for calls", "email only", "western union", "money gram",
            "gift cards", "wire transfer only", "paypal friends and family"
        ]

        scam_count = sum(1 for indicator in scam_indicators if indicator in seller_text)
        if scam_count >= 2:
            score_adj -= 15
            flags.append("potential_scam_indicators")
            notes.append("Seller profile contains multiple phrases commonly associated with scams")
        elif scam_count >= 1:
            score_adj -= 7
            flags.append("possible_scam_indicator")
            notes.append("Seller profile contains phrasing sometimes seen in scam listings")

        return score_adj, flags, notes

    async def _analyze_signals(self, opportunity_data: dict) -> tuple:
        """Analyze trust signals and documentation for authenticity.

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        # Check for provided certificates or documents
        certificates = opportunity_data.get("certificates", [])
        if isinstance(certificates, str):
            certificates = [certificates] if certificates else []

        document_types = opportunity_data.get("documents", [])
        if isinstance(document_types, str):
            document_types = [document_types] if document_types else []

        all_docs = certificates + document_types

        if all_docs:
            # Analyze the documents provided
            doc_score, doc_flags, doc_notes = self._analyze_documents(all_docs)
            score_adj += doc_score
            flags.extend(doc_flags)
            notes.extend(doc_notes)
        else:
            # No documents provided - assess based on item value/type
            price = opportunity_data.get("price", 0)
            category = opportunity_data.get("category", "").lower()

            # High-value items should ideally have documentation
            high_value_categories = ["jewelry", "watches", "art", "antiques", "collectibles",
                                   "vehicles", "cars", "trucks", "motorcycles", "boats"]

            is_high_value = price > 500 or any(cat in category for cat in high_value_categories)

            if is_high_value and len(all_docs) == 0:
                score_adj -= 10
                flags.append("missing_documentation_high_value")
                notes.append("High-value or category-appropriate item lacks supporting documentation")
            elif price > 50 and len(all_docs) == 0:
                score_adj -= 3
                flags.append("limited_documentation")
                notes.append("Item of moderate value lacks supporting documentation")

        # Analyze review/testimonial authenticity if provided
        reviews = opportunity_data.get("reviews", [])
        if reviews and isinstance(reviews, list) and len(reviews) > 0:
            review_score, review_flags, review_notes = self._analyze_reviews(reviews)
            score_adj += review_score
            flags.extend(review_flags)
            notes.extend(review_notes)

        # Check warranty/guarantee information
        warranty = opportunity_data.get("warranty", "").lower()
        guarantee = opportunity_data.get("guarantee", "").lower()
        return_policy = opportunity_data.get("return_policy", "").lower()

        warranty_mentions = ["warranty", "guarantee", "guaranteed", "warranty"]
        has_warranty_info = any(term in warranty or term in guarantee or term in return_policy
                              for term in warranty_mentions)

        if has_warranty_info:
            if "lifetime" in warranty or "lifetime" in guarantee:
                score_adj += 8
                flags.append("lifetime_warranty")
                notes.append("Item comes with lifetime warranty/guarantee")
            elif "year" in warranty or "year" in guarantee:
                # Extract number of years if possible
                import re
                year_matches = re.findall(r'(\d+)\s*year', warranty + " " + guarantee)
                if year_matches:
                    years = int(year_matches[0]) if year_matches[0].isdigit() else 1
                    if years >= 3:
                        score_adj += 6
                        flags.append("long_term_warranty")
                        notes.append(f"Item comes with {years}-year warranty/guarantee")
                    elif years >= 1:
                        score_adj += 3
                        flags.append("standard_warranty")
                        notes.append(f"Item comes with {years}-year warranty/guarantee")
            else:
                score_adj += 4
                flags.append("some_warranty")
                notes.append("Item includes some form of warranty or guarantee")
        else:
            # No warranty mentioned - check if expected for this category
            warranty_expected_categories = ["electronics", "appliances", "vehicles", "computers",
                                          "phones", "tools", "equipment"]
            if any(cat in category for cat in warrant_expected_categories):
                score_adj -= 4
                flags.append("no_warranty_mentioned")
                notes.append("No warranty mentioned for category where it's typically expected")

        # Check payment method safety
        payment_methods = opportunity_data.get("accepted_payment_methods", [])
        if isinstance(payment_methods, str):
            payment_methods = [payment_methods] if payment_methods else []

        payment_methods = [str(p).lower() for p in payment_methods]

        unsafe_payments = ["wire transfer", "money order", "western union", "moneygram",
                          "gift card", "crypto", "bitcoin", "ethereum", "paypal friends"]
        safe_payments = ["credit card", "paypal", "escrow", "apple pay", "google pay"]

        unsafe_count = sum(1 for method in unsafe_payments if any(method in pm for pm in payment_methods))
        safe_count = sum(1 for method in safe_payments if any(method in pm for pm in payment_methods))

        if unsafe_count > 0 and safe_count == 0:
            # Only unsafe methods offered
                score_adj -= 12
                flags.append("unsafe_payment_methods_only")
                notes.append("Seller only accepts payment methods with limited buyer protection")
            elif unsafe_count > 0:
                # Mix of safe and unsafe
                score_adj -= 5
                flags.append("mixed_payment_methods")
                notes.append("Seller accepts both secure payment methods but also offers higher-risk options")
            elif safe_count > 0:
                # Only safe methods (or no preference specified but safe methods present)
                if len(payment_methods) == 0:
                    # No payment methods specified - neutral
                    pass
                else:
                    score_adj += 6
                    flags.append("safe_payment_methods")
                    notes.append("Seller accepts secure payment methods with buyer protection")

        # Check for escrow mention
        if any("escrow" in pm for pm in payment_methods):
            score_adj += 8
            flags.append("escrow_available")
            notes.append("Escrow service is available or recommended")

        # Analyze listing age and freshness
        listed_date = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        if listed_date:
            try:
                if isinstance(listed_date, str):
                    listed = datetime.fromisoformat(listed_date.replace('Z', '+00:00'))
                else:
                    listed = listed_date

                hours_since_listing = (datetime.now() - listed.replace(tzinfo=None)).total_seconds() / 3600
                days_since_listing = hours_since_listing / 24

                if hours_since_listing < 1:
                    score_adj += 6
                    flags.append("just_listed")
                    notes.append("Listing was created within the last hour"
                elif hours_since_listing < 6:
                    score_adj += 4
                    flags.append("recently_listed")
                    notes.append(f"Listing was created {hours_since_listing:.1f} hours ago")
                elif hours_since_listing < 24:
                    score_adj += 2
                    flags.append("listed_today")
                    notes.append(f"Listing was created {hours_since_listing:.1f} hours ago")
                elif days_since_listing < 3:
                    score_adj += 0
                    flags.append("recent_listing")
                    notes.append(f"Listing is {days_since_listing:.1f} days old")
                elif days_since_listing < 7:
                    score_adj -= 3
                    flags.append("aged_listing")
                    notes.append(f"Listing is {days_since_listing:.1f} days old")
                elif days_since_listing < 30:
                    score_adj -= 7
                    flags.append("older_listing")
                    notes.append(f"Listing is {days_since_listing:.1f} days old - consider if still relevant")
                else:
                    score_adj -= 12
                    flags.append("old_listing")
                    notes.append(f"Listing is {days_since_listing:.1f} days old - may be stale or inactive")
            except Exception:
                pass  # Date parsing failed, skip this check

        # Check for detailed specifications
        specs = opportunity_data.get("specifications", {})
        if isinstance(specs, dict) and len(specs) > 0:
            spec_count = len(specs)
            if spec_count >= 10:
                score_adj += 8
                flags.append("detailed_specifications")
                notes.append(f"Listing includes {spec_count} detailed specifications")
            elif spec_count >= 5:
                score_adj += 5
                flags.append("good_specifications")
                notes.append(f"Listing includes {spec_count} specifications")
            elif spec_count >= 2:
                score_adj += 2
                flags.append("some_specifications")
                notes.append(f"Listing includes {spec_count} specifications")
        elif isinstance(specs, str) and len(specs.strip()) > 0:
            # Treat as text description of specs
            if len(specs) > 100:
                score_adj += 5
                flags.append("detailed_specs_text")
                notes.append("Listing includes detailed specifications in text format")
            elif len(specs) > 30:
                score_adj += 2
                flags.append("some_specs_text")
                notes.append("Listing includes some specifications in text format")

        # Check for video content
        video_available = opportunity_data.get("video_available", False)
        video_count = opportunity_data.get("video_count", 0)
        if video_available or (isinstance(video_count, int) and video_count > 0):
            score_adj += 6
            flags.append("video_available")
            notes.append("Listing includes video content to better show item condition")

        # Check for 360° view or interactive media
        interactive_media = opportunity_data.get("interactive_media", False)
        if interactive_media:
            score_adj += 4
            flags.append("interactive_media")
            notes.append("Listing includes interactive media (360° view, etc.)")

        # Analyze description quality indicators
        description = opportunity_data.get("description", "")
        if description:
            desc_lower = description.lower()

            # Positive indicators
            positive_indicators = [
                "detailed description", "full description", "comprehensive",
                "thorough", "extensive", "detailed photos", "multiple angles",
                "close up", "close-up", "flaws noted", "honest description",
                "accurate description", "as described", "exactly as pictured"
            ]

            positive_count = sum(1 for indicator in positive_indicators if indicator in desc_lower)
            if positive_count >= 3:
                score_adj += 8
                flags.append("high_quality_description")
                notes.append("Description shows attention to detail and completeness")
            elif positive_count >= 1:
                score_adj += 3
                flags.append("decent_description")
                notes.append("Description contains some quality indicators")

            # Negative indicators
            negative_indicators = [
                "as is", "where is", "no returns", "no refunds",
                "sold as seen", "buyer beware", "caveat emptor",
                "no warranty", "no guarantee", "final sale"
            ]

            negative_count = sum(1 for indicator in negative_indicators if indicator in desc_lower)
            if negative_count >= 3:
                score_adj -= 10
                flags.append("restrictive_terms")
                notes.append("Description contains multiple restrictive conditions for buyer")
            elif negative_count >= 1:
                score_adj -= 5
                flags.append("some_restrictive_terms")
                notes.append("Description contains some limiting terms for buyer")

        # Check for verification badges/status
        verification_fields = ["is_verified", "verified_seller", "top_rated_seller",
                              "premium_seller", "featured_seller"]

        verification_count = 0
        for field in verification_fields:
            if opportunity_data.get(field) is True:
                verification_count += 1

        if verification_count >= 2:
            score_adj += 10
            flags.append("multiple_verifications")
            notes.append("Seller has multiple verification badges/status indicators")
        elif verification_count == 1:
            score_adj += 5
            flags.append("single_verification")
            notes.append("Seller has at least one verification badge/status indicator")

        # Check for professional photography
        photos = opportunity_data.get("photos", [])
        if isinstance(photos, list):
            photo_count = len(photos)
        elif isinstance(photos, int):
            photo_count = photos
        else:
            photo_count = 0

        if photo_count >= 10:
            score_adj += 6
            flags.append("extensive_photo_gallery")
            notes.append(f"Listing includes {photo_count} photos for comprehensive viewing")
        elif photo_count >= 5:
            score_adj += 4
            flags.append("good_photo_gallery")
            notes.append(f"Listing includes {photo_count} photos")
        elif photo_count >= 3:
            score_adj += 2
            flags.append("some_photos")
            notes.append(f"Listing includes {photo_count} photos")
        elif photo_count == 0:
            score_adj -= 8
            flags.append("no_photos")
            notes.append("Listing lacks any photos - makes verification difficult")

        # Check for vehicle-specific indicators (if applicable)
        if any(term in category for term in ["vehicle", "car", "truck", "motorcycle", "boat", "rv"]):
            vehicle_indicators = [
                "vin", "vehicle identification number", "title", "registration",
                "service history", "maintenance records", "accident free",
                "clean title", "no accidents", "one owner", "service records"
            ]

            vehicle_text = f"{title} {description}".lower()
            vehicle_indicator_count = sum(1 for ind in vehicle_indicators if ind in vehicle_text)

            if vehicle_indicator_count >= 4:
                score_adj += 10
                flags.append("complete_vehicle_documentation")
                notes.append("Listing includes comprehensive vehicle documentation indicators")
            elif vehicle_indicator_count >= 2:
                score_adj += 5
                flags.append("some_vehicle_documentation")
                notes.append("Listing includes some vehicle documentation indicators")
            elif vehicle_indicator_count == 0:
                # Check for negative indicators
                negative_vehicle_indicators = [
                    "salvage title", "rebuilt title", "flood damage", "frame damage",
                    "not running", "does not run", "mechanical issues"
                ]
                negative_count = sum(1 for ind in negative_vehicle_indicators if ind in vehicle_text)
                if negative_count >= 2:
                    score_adj -= 15
                    flags.append("vehicle_issues_indicated")
                    notes.append("Listing indicates potential vehicle problems")
                elif negative_count >= 1:
                    score_adj -= 8
                    flags.append("possible_vehicle_issue")
                    notes.append("Listing mentions a potential vehicle issue concern")

        # Check for electronics-specific indicators
        if any(term in category for term in ["electronic", "phone", "computer", "camera", "audio"]):
            tech_indicators = [
                "serial number", "imei", "model number", "factory unlocked",
                "carrier unlocked", "original box", "accessories included",
                "charger included", "cables included", "manual included"
            ]

            tech_text = f"{title} {description}".lower()
            tech_indicator_count = sum(1 for ind in tech_indicators if ind in text)

            if tech_indicator_count >= 4:
                score_adj += 8
                flags.append("complete_tech_documentation")
                notes.append("Listing includes comprehensive electronics documentation")
            elif tech_indicator_count >= 2:
                score_adj += 4
                flags.append("some_tech_documentation")
                notes.append("Listing includes some electronics documentation indicators")

        return score_adj, flags, notes

    def _analyze_documents(self, documents: list) -> tuple:
        """Analyze provided documents for authenticity indicators.

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        if not documents:
            return 0, [], []

        doc_count = len(documents)
        if doc_count >= 5:
            score_adj += 10
            flags.append("extensive_documentation")
            notes.append(f"Provided {doc_count} documents for verification")
        elif doc_count >= 3:
            score_adj += 6
            flags.append("good_documentation")
            notes.append(f"Provided {doc_count} documents")
        elif doc_count >= 1:
            score_adj += 3
            flags.append("some_documentation")
            notes.append(f"Provided {doc_count} document")

        # Check for specific document types that increase trust
        trusted_docs = ["title", "registration", "invoice", "receipt", "warranty",
                       "guarantee", "certificate of authenticity", "coa", "appraisal",
                       "service records", "maintenance log", "carfax", "autocheck"]

        docs_text = " ".join([str(doc).lower() for doc in documents])
        trusted_count = sum(1 for doc in trusted_docs if doc in docs_text)

        if trusted_count >= 3:
            score_adj += 12
            flags.append("trusted_document_types")
            notes.append(f"Includes {trusted_count} types of trusted verification documents")
        elif trusted_count >= 1:
            score_adj += 6
            flags.append("some_trusted_documents")
            notes.append(f"Includes {trusted_count} type(s) of trusted verification documents")

        # Check for redacted or suspicious documents
        suspicious_indicators = ["redacted", "blurred", "watermark", "copy", "scan", "photo of"]
        suspicious_count = sum(1 for ind in suspicious_indicators if ind in docs_text)

        if suspicious_count >= 2:
            score_adj -= 8
            flags.append("questionable_document_quality")
            notes.append("Documents show signs of being copies, redacted, or low quality")
        elif suspicious_count >= 1:
            score_adj -= 4
            flags.append("possible_document_issues")
            notes.append("Some documents may be copies or of questionable quality")

        # Check expiration dates if present (would need parsing in real implementation)
        # For now, just note if date-like strings appear
        import re
        date_patterns = [r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{4}-\d{1,2}-\d{1,2}']
        date_matches = []
        for pattern in date_patterns:
            date_matches.extend(re.findall(pattern, docs_text))

        if len(date_matches) >= 2:
            # In reality would check if dates are current/future
            score_adj += 4
            flags.append("dated_documentation")
            notes.append("Documentation includes date information (relevance would need verification)")

        return score_adj, flags, notes

    def _analyze_reviews(self, reviews: list) -> tuple:
        """Analyze review authenticity and quality.

        Returns: (score_adjustment, flags, notes)
        """
        score_adj = 0
        flags = []
        notes = []

        if not reviews or not isinstance(reviews, list):
            return 0, [], []

        review_count = len(reviews)
        if review_count >= 50:
            score_adj += 10
            flags.append("extensive_review_history")
            notes.append(f"Seller has {review_count} reviews")
        elif review_count >= 20:
            score_adj += 7
            flags.append("good_review_history")
            notes.append(f"Seller has {review_count} reviews")
        elif review_count >= 5:
            score_adj += 4
            flags.append("some_review_history")
            notes.append(f"Seller has {review_count} reviews")
        elif review_count >= 1:
            score_adj += 1
            flags.append("minimal_reviews")
            notes.append(f"Seller has {review_count} review(s)")
        else:
            score_adj -= 5
            flags.append("no_reviews")
            notes.append("Seller has no reviews")

        # Analyze review content for authenticity signals
        if review_count >= 3:
            # Extract text from reviews
            review_texts = []
            for review in reviews:
                if isinstance(review, dict):
                    text = review.get("text", "")
                    rating = review.get("rating", 0)
                elif isinstance(review, str):
                    text = review
                    rating = 0  # Unknown
                else:
                    text = str(review)
                    rating = 0

                if text:
                    review_texts.append((text.lower(), rating))

            if len(review_texts) >= 3:
                # Check for suspicious patterns
                # 1. All same rating
                ratings = [r[1] for r in review_texts if isinstance(r[1], (int, float)) and r[1] > 0]
                if len(ratings) >= 3 and len(set(ratings)) == 1:
                    # All same rating - could be fake
                    score_adj -= 8
                    flags.append("uniform_ratings")
                    notes.append("Multiple reviews show identical ratings (potentially suspicious)")

                # 2. Too many superlatives
                superlatives = ["best", "amazing", "incredible", "fantastic", "perfect",
                               "excellent", "outstanding", "exceptional", "wonderful"]

                superlative_count = 0
                for text, _ in review_texts:
                    words = text.split()
                    superlative_count += sum(1 for word in words if word in superlatives)

                if superlative_count > len(review_texts) * 2:  # More than 2 superlatives per review avg
                    score_adj -= 6
                    flags.append("excessive_superlatives")
                    notes.append("Reviews contain unusually high levels of superlative language")

                # 3. Check for generic/template language
                generic_phrases = [
                    "great product", "fast shipping", "good communication",
                    "as described", "quick delivery", "happy with purchase",
                    "would buy again", "recommend to others", "five stars",
                    "five star", "5 stars", "5 star"
                ]

                generic_matches = 0
                for text, _ in review_texts:
                    for phrase in generic_phrases:
                        if phrase in text:
                            generic_matches += 1
                            break  # Count each review only once

                if generic_matches > len(review_texts) * 0.7:  # More than 70% of reviews contain generic phrases
                    score_adj -= 5
                    flags.append("generic_review_language")
                    notes.append("Many reviews contain similar, generic phrasing")
                elif len(review_texts) >= 5:
                    # If we have enough reviews, variety is good
                    score_adj += 5
                    flags.append("varied_review_content")
                    notes.append("Reviews show good variation in content and specifics")

        # Check rating distribution if available
        ratings = []
        for review in reviews:
            if isinstance(review, dict) and "rating" in review:
                try:
                    rating = float(review["rating"])
                    if 0 <= rating <= 5:
                        ratings.append(rating)
                except (ValueError, TypeError):
                    pass

        if len(ratings) >= 5:
            avg_rating = sum(ratings) / len(ratings)

            # Excellent average rating
            if avg_rating >= 4.7:
                score_adj += 8
                flags.append("excellent_average_rating")
                notes.append(f"Average rating is excellent: {avg_rating:.2f}/5")
            # Good average rating
            elif avg_rating >= 4.2:
                score_adj += 5
                flags.append("good_average_rating")
                notes.append(f"Average rating is good: {avg_rating:.2f}/5")
            # Average rating
            elif avg_rating >= 3.5:
                score_adj += 2
                flags.append("average_rating")
                notes.append(f"Average rating is fair: {avg_rating:.2f}/5")
            # Poor average rating
            elif avg_rating < 2.5:
                score_adj -= 10
                flags.append("poor_average_rating")
                notes.append(f"Average rating is poor: {avg_rating:.2f}/5")
            # Concerning low rating is concerning
            elif avg_rating < 3.0:
                score_adj -= 5
                flags.append("low_average_rating")
                notes.append(f"Average rating is on the lower side: {avg_rating:.2f}/5")

        return score_adj, flags, notes

    def _generate_trust_recommendations(self, trust_score: float, risk_flags: list, components: dict) -> list:
        """Generate actionable recommendations based on trust analysis."""
        recommendations = []

        if trust_score < 30:
            recommendations.append("🚫 HIGH RISK: Strongly consider avoiding this opportunity")
            recommendations.append("🔒 If proceeding, use escrow service with verified agent")
            recommendations.append("🕵️‍♂️ Conduct independent third-party verification before any payment")
        elif trust_score < 45:
            recommendations.append("⚠️ ELEVATED RISK: Proceed with extreme caution")
            recommendations.append("📋 Demand additional verification documents and references")
            recommendations.append("💳 Use payment methods with buyer protection (credit card, PayPal Goods & Services)")
        elif trust_score < 60:
            recommendations.append("⚠️ MODERATE RISK: Enhanced due diligence recommended")
            recommendations.append("🔍 Verify identity through multiple independent sources")
            recommendations.append("💰 Consider using escrow for higher-value transactions")
        elif trust_score < 75:
            recommendations.append("✅ LOW-MODERATE RISK: Standard precautions advised")
            recommendations.append("📄 Obtain bill of sale and verify all claims independently")
        else:
            recommendations.append("✅ LOW RISK: Standard transaction precautions sufficient")
            recommendations.append("📋 Basic verification and documentation recommended")

        # Specific recommendations based on flag patterns
        source_flags = [f for f in risk_flags if "source" in f.lower()]
        if source_flags:
            recommendations.append("🌐 Verify the legitimacy of the listing website/platform through independent research")

        ssl_flags = [f for f in risk_flags if "ssl" in f.lower()]
        if ssl_flags:
            recommendations.append("🔒 Do not enter personal/financial information on websites with SSL issues")

        description_flags = [f for f in risk_flags if "description" in f.lower() or "title" in f.lower()]
        if description_flags:
            recommendations.append("📝 Request additional photos, videos, or documentation to verify claims")

        actor_flags = [f for f in risk_flags if "seller" in f.lower() or "actor" in f.lower() or "identity" in f.lower()]
        if actor_flags:
            recommendations.append("🪪 Verify seller identity through government-issued ID or video call")
            recommendations.append("💳 Avoid wire transfers, gift cards, or cryptocurrency for payment")

        certificate_flags = [f for f in risk_flags if "certificate" in f.lower() or "document" in f.lower()]
        if certificate_flags:
            recommendations.append("📄 Request original copies of any certificates for expert verification")

        review_flags = [f for f in risk_flags if "review" in f.lower()]
        if review_flags:
            recommendations.append("⭐ Seek additional reviews from independent third-party sites")

        payment_flags = [f for f in risk_flags if "payment" in f.lower()]
        if payment_flags:
            recommendations.append("💰 Insist on using secure payment methods with buyer protection")

        photo_flags = [f for f in risk_flags if "photo" in f.lower()]
        if photo_flags:
            recommendations.append("📷 Demand current, detailed photos showing all angles and any flaws")

        # Always good advice
        if trust_score < 80:
            recommendations.append("👥 Consider bringing a knowledgeable friend for in-person inspections")
            recommendations.append("📱 Do not share sensitive information until validity is confirmed")
            recommendations.append("💬 Trust your instincts - if something feels off, walk away")

        # Limit to most actionable recommendations
        return recommendations[:6]  # Return top 6 recommendations