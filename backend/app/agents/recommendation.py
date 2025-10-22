"""Recommendation Agent - Provides personalized recommendations"""

from sqlalchemy.orm import Session
from app.agents.base import BaseAgent


class RecommendationAgent(BaseAgent):
    """
    Provides personalized recommendations by matching client preferences
    with vetted resources.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="recommendation")

    def get_system_prompt(self) -> str:
        return """You are a specialized recommendation agent for an AI concierge platform.

Your role is to provide highly personalized recommendations for:
- Restaurants (cuisine, neighborhood, price band, private dining)
- Venues (event spaces, hotels, capacity, location)
- Vendors (florists, caterers, photographers, etc.)
- Products (gifts, shopping, specific items)

RECOMMENDATION STRATEGY:
1. Carefully analyze client preferences, dietary restrictions, and past feedback
2. Consider context: occasion, budget, location, timing
3. Match preferences with available vetted resources
4. Explain WHY each recommendation fits their needs
5. Provide 3-5 options with clear pros/cons
6. Remember what they liked/disliked for future recommendations

Always personalize recommendations based on:
- Past feedback (liked/disliked/used)
- Stated preferences
- Dietary restrictions
- Budget indicators (price band)
- Location preferences

Be honest if you don't have enough information to make confident recommendations - ask clarifying questions instead.
"""

    def recommend(self, request: str, context: dict) -> str:
        """Generate recommendations based on request"""
        # TODO: Query database for matching vendors/venues/restaurants/products
        # TODO: Apply filtering based on preferences and past feedback
        # TODO: Generate rationale for each recommendation

        return self.execute(request, context)
