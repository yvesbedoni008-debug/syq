"""Discovery Agent: finds opportunities across data sources."""

from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DiscoveryAgent(BaseAgent):
    """Agent responsible for discovering new opportunities from various sources."""

    def __init__(self):
        super().__init__("DiscoveryAgent")
        # Source reliability scores (in production, these would be dynamically updated)
        self.source_reliability = {
            "official_auction_house": 0.95,
            "manufacturer_direct": 0.9,
            "authorized_dealer": 0.85,
            "established_marketplace": 0.8,
            "industry_specialist": 0.75,
            "trade_show_exhibitor": 0.7,
            "online_classifieds": 0.5,
            "social_media": 0.4,
            "unknown_source": 0.2
        }

    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Discover opportunities or enrich existing ones with discovery insights.

        For now, returns a detailed discovery analysis based on available data.
        In production, this would query external APIs, scrapers, and databases.
        """
        self._log_info("Processing opportunity discovery")

        # Analyze the opportunity source and metadata
        discovery_score = 50  # Start with neutral score
        confidence_factors = []
        flags = []
        notes = []

        # 1. Source Analysis
        source_score, source_notes, source_flags = self._analyze_source(opportunity_data)
        discovery_score += source_score
        notes.extend(source_notes)
        flags.extend(source_flags)

        # 2. Temporal Analysis (how recent/fresh is the opportunity?)
        time_score, time_notes, time_flags = self._analyze_timeliness(opportunity_data)
        discovery_score += time_score
        notes.extend(time_notes)
        flags.extend(time_flags)

        # 3. Content Analysis (quality and completeness of listing)
        content_score, content_notes, content_flags = self._analyze_content(opportunity_data)
        discovery_score += content_score
        notes.extend(content_notes)
        flags.extend(content_flags)

        # 4. Uniqueness Analysis (how unique or common is this opportunity?)
        uniqueness_score, uniqueness_notes, uniqueness_flags = self._analyze_uniqueness(opportunity_data)
        discovery_score += uniqueness_score
        notes.extend(uniqueness_notes)
        flags.extend(uniqueness_flags)

        # 5. Geographic Analysis (if location data available)
        geo_score, geo_notes, geo_flags = self._analyze_geography(opportunity_data)
        discovery_score += geo_score
        notes.extend(geo_notes)
        flags.extend(geo_flags)

        # Ensure score stays within bounds
        discovery_score = max(0, min(100, discovery_score))

        # Calculate confidence based on data quality
        confidence = self._calculate_discovery_confidence(opportunity_data, confidence_factors)

        # Generate discovery insights and recommendations
        insights = self._generate_discovery_insights(
            discovery_score,
            {
                "source": source_score,
                "temporal": time_score,
                "content": content_score,
                "uniqueness": uniqueness_score,
                "geographic": geo_score
            },
            notes
        )
        recommendations = self._generate_discovery_recommendations(discovery_score, flags)

        return {
            "agent": self.agent_name,
            "discovery_score": round(discovery_score, 1),
            "confidence": round(confidence, 2),
            "factors": {
                "source_reliability": source_score,
                "timeliness": time_score,
                "content_quality": content_score,
                "uniqueness": uniqueness_score,
                "geographic_relevance": geo_score
            },
            "flags": list(set(flags)),  # Remove duplicates
            "insights": insights,
            "notes": "; ".join(notes) if notes else "Discovery analysis completed",
            "suggested_actions": recommendations
        }

    def _analyze_source(self, opportunity_data: dict) -> tuple:
        """Analyze the reliability and credibility of the opportunity source."""
        score = 0
        notes = []
        flags = []

        source = opportunity_data.get("source", "").lower().strip()
        platform = opportunity_data.get("platform", "").lower().strip()
        url = opportunity_data.get("url", "").lower()

        # Check explicit source
        source_to_check = source or platform or url

        if source_to_check:
            # Direct match in our reliability database
            for known_source, reliability in self.source_reliability.items():
                if known_source in source_to_check:
                    score += int((reliability - 0.5) * 40)  # -20 to +20 points
                    if reliability > 0.7:
                        flags.append(f"reliable_source:{known_source}")
                    else:
                        flags.append(f"unreliable_source:{known_source}")
                    notes.append(f"Source identified as '{known_source}' with reliability {reliability}")
                    break
            else:
                # No direct match - analyze characteristics
                if "api" in source_to_check or "feed" in source_to_check:
                    score += 10
                    flags.append("api_source")
                    notes.append("Source appears to be an automated feed or API")
                elif any(social in source_to_check for social in ["facebook", "twitter", "instagram", "linkedin"]):
                    score -= 15
                    flags.append("social_media_source")
                    notes.append("Source is social media - verify independently")
                elif "forum" in source_to_check or "board" in source_to_check:
                    score -= 5
                    flags.append("forum_source")
                    notes.append("Source is a forum - mixed reliability")
                else:
                    score -= 10
                    flags.append("unknown_characteristics")
                    notes.append("Source characteristics not recognized")

        # Check for official identifiers
        if opportunity_data.get("license_number") or opportunity_data.get("registration_id"):
            score += 15
            flags.append("registered_entity")
            notes.append("Opportunity source has official registration/license")

        if opportunity_data.get("vat_number") or opportunity_data.get("tax_id"):
            score += 10
            flags.append("tax_registered")
            notes.append("Source appears to be tax-registered business")

        return score, notes, flags

    def _analyze_timeliness(self, opportunity_data: dict) -> tuple:
        """Analyze how timely/fresh the opportunity is."""
        score = 0
        notes = []
        flags = []

        # Check listing date
        listed_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        if listed_str:
            try:
                if isinstance(listed_str, str):
                    listed_date = datetime.fromisoformat(listed_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_str

                days_old = (datetime.now() - listed_date.replace(tzinfo=None)).days

                if days_left < 1:
                    score += 10
                    flags.append("just_listed")
                    notes.append("Opportunity was listed within the last 24 hours")
                elif days_old < 7:
                    score += 5
                    flags.append("recent_listing")
                    notes.append(f"Opportunity listed {days_old} days ago")
                elif days_old < 30:
                    score += 0
                    flags.append("moderate_age")
                    notes.append(f"Opportunity listed {days_old} days ago")
                elif days_old < 90:
                    score -= 5
                    flags.append("aging_listing")
                    notes.append(f"Opportunity listed {days_old} days ago - consider if still relevant")
                else:
                    score -= 15
                    flags.append("stale_listing")
                    notes.append(f"Opportunity listed {days_old} days ago - likely stale")
            except Exception as e:
                self._log_debug(f"Date parsing failed: {e}")
                pass  # Could not parse date

        # Check for expiration or validity period
        expires_str = opportunity_data.get("expires_at") or opportunity_data.get("valid_until")
        if expires_str:
            try:
                if isinstance(expires_str, str):
                    expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                else:
                    expires_date = expires_str

                days_until_expiry = (expires_date.replace(tzinfo=None) - datetime.now()).days

                if days_until_expiry < 0:
                    score -= 20
                    flags.append("expired")
                    notes.append("Opportunity has expired")
                elif days_until_expiry < 3:
                    score -= 10
                    flags.append("expiring_soon")
                    notes.append(f"Opportunity expires in {days_until_expiry} days")
                elif days_until_expiry < 14:
                    score += 5
                    flags.append("limited_time")
                    notes.append(f"Opportunity available for {days_until_expiry} more days")
                else:
                    score += 0
                    flags.append("valid_period")
                    notes.append(f"Opportunity valid for {days_until_expiry} more days")
            except Exception as e:
                self._log_debug(f"Expiry date parsing failed: {e}")
                pass

        return score, notes, flags

    def _analyze_content(self, opportunity_data: dict) -> tuple:
        """Analyze the quality and completeness of the opportunity listing."""
        score = 0
        notes = []
        flags = []

        # Check title quality
        title = opportunity_data.get("title", "")
        if title:
            if len(title) >= 10:
                score += 5
                flags.append("adequate_title_length")
            else:
                score -= 5
                flags.append("short_title")
                notes.append("Title is quite short - may lack important details")

            # Check for marketing language vs factual description
            marketing_terms = ["amazing", "incredible", "unbelievable", "best ever", "must see"]
            factual_terms = ["specification", "model", "year", "condition", "mileage", "hours"]

            title_lower = title.lower()
            marketing_count = sum(1 for term in marketing_terms if term in title_lower)
            factual_count = sum(1 for term in factual_terms if term in title_lower)

            if factual_count > marketing_count:
                score += 5
                flags.append("factual_title")
                notes.append("Title appears to focus on factual details")
            elif marketing_count > factual_count and marketing_count > 0:
                score -= 5
                flags.append("hype_title")
                notes.append("Title contains promotional language - verify claims")
        else:
            score -= 10
            flags.append("missing_title")
            notes.append("Opportunity missing title")

        # Check description quality
        description = opportunity_data.get("description", "")
        if description:
            desc_length = len(description)
            if desc_length >= 100:
                score += 10
                flags.append("detailed_description")
            elif desc_length >= 50:
                score += 5
                flags.append("adequate_description")
            elif desc_length >= 20:
                score += 0
                flags.append("basic_description")
            else:
                score -= 5
                flags.append("brief_description")
                notes.append("Description is quite brief")

            # Check for structured information
            structured_indicators = ["specs:", "details:", "features:", "condition:", "year:", "model:"]
            struct_count = sum(1 for indicator in structured_indicators if indicator in description.lower())
            if struct_count >= 3:
                score += 10
                flags.append("well_structured")
                notes.append("Description contains well-organized sections")
            elif struct_count >= 1:
                score += 5
                flags.append("some_structure")
                notes.append("Description has some structural elements")
        else:
            score -= 15
            flags.append("missing_description")
            notes.append("No description provided")

        # Check for multimedia
        images = opportunity_data.get("images", [])
        if isinstance(images, list):
            if len(images) >= 5:
                score += 10
                flags.append("multiple_images")
                notes.append(f"Opportunity includes {len(images)} images")
            elif len(images) >= 1:
                score += 5
                flags.append("has_images")
                notes.append(f"Opportunity includes {len(images)} image(s)")
            else:
                score -= 5
                flags.append("no_images")
                notes.append("No images provided - harder to verify condition")
        elif images and isinstance(images, int) and images > 0:
            score += 5
            flags.append("has_image_count")
            notes.append(f"Opportunity indicates {images} images available")

        # Check for pricing transparency
        price = opportunity_data.get("price")
        if price is not None and isinstance(price, (int, float)) and price > 0:
            score += 10
            flags.append("price_specified")
            notes.append("Price is clearly specified")
        elif opportunity_data.get("price_negotiable") is True:
            score += 0
            flags.append("price_negotiable")
            notes.append("Price is marked as negotiable")
        else:
            score -= 10
            flags.append("price_unspecified")
            notes.append("Price not specified or unclear")

        return score, notes, flags

    def _analyze_uniqueness(self, opportunity_data: dict) -> tuple:
        """Analyze how unique or common this opportunity appears to be."""
        score = 0
        notes = []
        flags = []

        # Check for rarity indicators
        rare_indicators = [
            "limited edition", "rare", "one of", "only", "few exist",
            "discontinued", "vintage", "antique", "collectible",
            "prototype", "prototype", "pre-production"
        ]

        common_indicators = [
            "bulk", "lot", "pallet", "wholesale", "quantity", "multiple units",
            "batch", "inventory overstock", "clearance"
        ]

        text_to_check = f"{opportunity_data.get('title', '')} {opportunity_data.get('description', '')}".lower()

        rare_count = sum(1 for indicator in rare_indicators if indicator in text_to_check)
        common_count = sum(1 for indicator in common_indicators if indicator in text_to_check)

        if rare_count > 0:
            score += min(15, rare_count * 5)  # Up to +15 for rarity
            flags.append("rare_item")
            notes.append(f"Opportunity appears to be rare ({rare_count} rarity indicators)")
        elif common_count > 0:
            score -= min(10, common_count * 3)  # Up to -10 for commonality
            flags.append("common_item")
            notes.append(f"Opportunity appears to be commonly available ({common_count} common indicators)")

        # Check for unique identifiers
        if opportunity_data.get("vin") or opportunity_data.get("serial_number"):
            score += 10
            flags.append("unique_identifier")
            notes.append("Opportunity has unique identification number (VIN/serial)")

        if opportunity_data.get("lot_number") or opportunity_data.get("batch_id"):
            score += 5
            flags.append("batch_identified")
            notes.append("Opportunity part of identifiable batch/lot")

        # Check if it matches specific search criteria (would come from context)
        # This would be more sophisticated in production with actual search history

        return score, notes, flags

    def _analyze_geography(self, opportunity_data: dict) -> tuple:
        """Analyze geographic factors if location data is available."""
        score = 0
        notes = []
        flags = []

        location = opportunity_data.get("location", "").lower()
        if not location:
            location = opportunity_data.get("seller_location", "").lower()
            if not location:
                location = opportunity_data.get("ship_from", "").lower()

        if location:
            # Check for local vs international
            local_indicators = ["localhost", "127.0.0.1", "local"]
            if any(indicator in location for indicator in local_indicators):
                score += 5
                flags.append("local_source")
                notes.append("Source appears to be local")
            else:
                # In reality, we'd do geolocation and distance calculation
                # For now, just note that location is specified
                score += 3
                flags.append("location_specified")
                notes.append(f"Location specified: {location}")

            # Check for known logistics hubs (better shipping)
            logistics_hubs = ["rotterdam", "singapore", "shanghai", "los angeles", "hamburg"]
            if any(hub in location for hub in logistics_hubs):
                score += 5
                flags.append("logistics_hub")
                notes.append("Located near major logistics hub - favorable shipping")
        else:
            score -= 5
            flags.append("no_location")
            notes.append("No location information provided")

        # Check for shipping/restrictions info
        restrictions = opportunity_data.get("shipping_restrictions", "")
        if restrictions:
            if "worldwide" in restrictions.lower() or "international" in restrictions.lower():
                score += 5
                flags.append("ships_internationally")
                notes.append("Item can be shipped internationally")
            elif "local pickup only" in restrictions.lower():
                score -= 10
                flags.append("local_pickup_only")
                notes.append("Item available for local pickup only - limits buyer pool")
        elif opportunity_data.get("local_pickup_only") is True:
            score -= 10
            flags.append("local_pickup_only")
            notes.append("Item available for local pickup only - limits buyer pool")

        return score, notes, flags

    def _calculate_discovery_confidence(self, opportunity_data: dict, factors: list) -> float:
        """Calculate confidence in the discovery analysis based on data quality."""
        base_confidence = 0.6  # Base confidence

        # Increase confidence for complete data
        required_fields = ["title", "description", "source", "price"]
        present_fields = sum(1 for field in required_fields if opportunity_data.get(field) is not None)
        completeness_bonus = (present_fields / len(required_fields)) * 0.3  # Up to +0.3

        # Increase confidence for recent data
        listed_str = opportunity_data.get("listed_date") or opportunity_data.get("created_at")
        if listed_str:
            try:
                if isinstance(listed_str, str):
                    listed_date = datetime.fromisoformat(listed_str.replace('Z', '+00:00'))
                else:
                    listed_date = listed_str

                hours_old = (datetime.now() - listed_date.replace(tzinfo=None)).total_seconds() / 3600
                if hours_old < 24:
                    recency_bonus = 0.1  # +0.1 for very recent
                elif hours_old < 168:  # Less than a week
                    recency_bonus = 0.05  # +0.05 for recent
                else:
                    recency_bonus = 0.0  # No bonus for older data
            except Exception:
                recency_bonus = 0.0
        else:
            recency_bonus = -0.1  # Penalty for no date

        # Calculate final confidence
        confidence = base_confidence + completeness_bonus + recency_bonus
        return max(0.1, min(0.95, confidence))  # Clamp between 0.1 and 0.95

    def _generate_discovery_insights(self, score: float, factors: dict, notes: list) -> list:
        """Generate insights from the discovery analysis."""
        insights = []

        # Overall assessment
        if score >= 80:
            insights.append("High-discovery confidence opportunity from reliable source")
        elif score >= 60:
            insights.append("Good discovery opportunity with reliable indicators")
        elif score >= 40:
            insights.append("Moderate discovery opportunity - verify key details")
        else:
            insights.append("Low-discovery confidence - requires extensive verification")

        # Source-specific insights
        if factors.get("source", 0) > 10:
            insights.append("Opportunity comes from a highly reliable source")
        elif factors.get("source", 0) < -10:
            insights.append("Source reliability is questionable - seek corroboration")

        # Timeliness insights
        if factors.get("temporal", 0) > 10:
            insights.append("Recently listed opportunity - may represent fresh market entry")
        elif factors.get("temporal", 0) < -10:
            insights.append("Listing has been active for some time - market may have responded")

        # Content insights
        if factors.get("content", 0) > 15:
            insights.append("Well-documented listing with comprehensive details")
        elif factors.get("content", 0) < -10:
            insights.append("Sparse listing details - request additional information")

        # Uniqueness insights
        if factors.get("uniqueness", 0) > 10:
            insights.append("Appears to be a rare or distinctive opportunity")
        elif factors.get("uniqueness", 0) < -10:
            insights.append("Appears to be a common offering - verify competitive pricing")

        return insights[:4]  # Limit to top 4 insights

    def _generate_discovery_recommendations(self, score: float, flags: list) -> list:
        """Generate actionable recommendations based on discovery analysis."""
        recommendations = []

        if score >= 80:
            recommendations.append("Prioritize for immediate review - high-discovery confidence")
            recommendations.append("Consider allocating resources for deep-dive analysis")
        elif score >= 60:
            recommendations.append("Schedule for standard review process")
            recommendations.append("Verify key details before proceeding to valuation")
        elif score >= 40:
            recommendations.append("Conduct preliminary verification before deep analysis")
            recommendations.append("Focus on validating source and basic facts")
        else:
            recommendations.append("Treat as low-priority unless compelling reason to investigate")
            recommendations.append("Require multiple independent verifications before proceeding")

        # Specific recommendations based on issues
        if any("no_images" in flag for flag in flags):
            recommendations.append("Request visual documentation before serious consideration")

        if any("price_unspecified" in flag for flag in flags):
            recommendations.append("Obtain clear pricing before proceeding")

        if any("missing_description" in flag for flag in flags):
            recommendations.append("Request detailed description of the opportunity")

        if any("local_pickup_only" in flag for flag in flags):
            recommendations.append("Factor in logistics costs and feasibility for remote buyers")

        if any("stale_listing" in flag for flag in flags):
            recommendations.append("Verify opportunity is still available before investing time")

        return recommendations[:5]  # Limit to top 5 recommendations