"""Intent-based search endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import OpportunityService
from app.schemas import IntentRequest, IntentResponse, OpportunityExplanation
from app.core.security import get_current_user
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=IntentResponse)
async def intent_search(
    request: IntentRequest,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process natural language search queries to find relevant opportunities
    Example: "I want a reliable sports car under 40k that holds its value"
    """
    opportunity_service = OpportunityService(db)

    # Parse the natural language query (simplified for MVP)
    query_lower = request.query.lower()

    # Extract filters from natural language
    filters = {}

    # Price extraction patterns
    price_patterns = [
        (r'under\s*\$?(\d+(?:,\d+)*)', 'max_price'),
        (r'below\s*\$?(\d+(?:,\d+)*)', 'max_price'),
        (r'less\s*than\s*\$?(\d+(?:,\d+)*)', 'max_price'),
        (r'over\s*\$?(\d+(?:,\d+)*)', 'min_price'),
        (r'above\s*\$?(\d+(?:,\d+)*)', 'min_price'),
        (r'more\s*than\s*\$?(\d+(?:,\d+)*)', 'min_price'),
        (r'between\s*\$?(\d+(?:,\d+)*)\s*and\s*\$?(\d+(?:,\d+)*)', 'price_range')
    ]

    for pattern, field in price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if field == 'price_range':
                min_val = int(match.group(1).replace(',', ''))
                max_val = int(match.group(2).replace(',', ''))
                filters['min_price'] = min_val * 100  # Assuming price is in cents
                filters['max_price'] = max_val * 100
            else:
                val = int(match.group(1).replace(',', ''))
                if field in ['min_price', 'max_price']:
                    filters[field] = val * 100  # Convert to cents
                break  # Only use the first match

    # Category detection
    categories = {
        'car': ['car', 'auto', 'automobile', 'vehicle', 'truck', 'suv', 'sedan', 'coupe', 'convertible'],
        'electronics': ['phone', 'smartphone', 'laptop', 'computer', 'tablet', 'tv', 'television', 'camera'],
        'fashion': ['clothing', 'clothes', 'shoes', 'sneakers', 'jacket', 'dress', 'watch', 'jewelry'],
        'home': ['furniture', 'couch', 'sofa', 'bed', 'table', 'chair', 'appliance'],
        'sports': ['bike', 'bicycle', 'golf', 'ski', 'surf', 'exercise', 'fitness'],
        'real_estate': ['house', 'home', 'apartment', 'condo', 'land', 'property', 'real estate']
    }

    for category, keywords in categories.items():
        if any(keyword in query_lower for keyword in keywords):
            # Map to standard categories
            category_map = {
                'car': 'Vehicles',
                'electronics': 'Electronics',
                'fashion': 'Fashion',
                'home': 'Home & Garden',
                'sports': 'Sports & Outdoors',
                'real_estate': 'Real Estate'
            }
            filters['category'] = category_map.get(category, category.title())
            break

    # Condition/quality indicators
    if any(word in query_lower for word in ['new', 'like new', 'excellent']):
        filters['condition'] = 'new'
    elif any(word in query_lower for word in ['used', 'pre-owned', 'secondhand']):
        filters['condition'] = 'used'
    elif any(word in query_lower for word in ['refurbished', 'reconditioned']):
        filters['condition'] = 'refurbished'

    # Get opportunities based on parsed criteria
    try:
        results = await opportunity_service.get_opportunity_feed(
            user_id=getattr(current_user, 'id', None) if current_user else None,
            skip=0,
            limit=20,
            filters=filters
        )
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing search request"
        )

    # Generate explanations for each result
    explanations = []
    for opp_data in results["opportunities"]:
        opportunity = opp_data["opportunity"]
        score = opp_data["score"]

        # Build explanation based on match quality
        what_is_happening = f"Found {opportunity.title}"
        if opportunity.category:
            what_is_happening += f" in the {opportunity.category} category"
        if opportunity.price:
            what_is_happening += f" priced at ${opportunity.price // 100}"

        why_it_matters = f"This matches your search for '{request.query}'"
        if score:
            why_it_matters += f" with a SYQ Score of {score.overall_score}/100"

        # Confidence based on score confidence and match quality
        confidence_level = "Medium"
        if score:
            if score.confidence_score >= 80:
                confidence_level = "High"
            elif score.confidence_score >= 50:
                confidence_level = "Medium"
            else:
                confidence_level = "Low"

        # Identify potential risks
        risks = []
        if not opportunity.description:
            risks.append("Limited description available")
        if not opportunity.source:
            risks.append("Source not specified")
        if score and score.confidence_score < 50:
            risks.append("Low confidence in data quality")

        # Considerations for the user
        considerations = []
        if opportunity.price:
            considerations.append(f"Price: ${opportunity.price // 100}")
        if opportunity.market_value:
            savings = opportunity.market_value - opportunity.price
            if savings > 0:
                considerations.append(f"You save ${savings // 100} vs market value")
            else:
                considerations.append(f"Above market value by ${abs(savings) // 100}")
        if opportunity.source:
            considerations.append(f"Source: {opportunity.source}")

        explanations.append(OpportunityExplanation(
            what_is_happening=what_is_happening,
            why_it_matters=why_it_matters,
            confidence_level=confidence_level,
            risks=risks,
            considerations=considerations
        ))

    # Log the search for analytics
    try:
        audit_service = AuditLogRepository(db)
        await audit_service.create(
            action="intent_search",
            user_id=getattr(current_user, 'id', None) if current_user else None,
            details=f"Query: '{request.query}' | Results: {len(results['opportunities'])} | Filters: {filters}"
        )
    except Exception as e:
        logger.warning(f"Failed to log search: {e}")

    return IntentResponse(
        opportunities=[opp_data["opportunity"] for opp_data in results["opportunities"]],
        explanations=explanations,
        query_interpretation={
            "original_query": request.query,
            "normalized_query": query_lower,
            "extracted_filters": filters,
            "timestamp": datetime.utcnow().isoformat()
        }
    )