"""Data Capture Agent - Extracts structured information from conversations"""

from sqlalchemy.orm import Session
from app.agents.base import BaseAgent


class DataCaptureAgent(BaseAgent):
    """
    Extracts structured information from unstructured conversations
    for database enrichment.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="data_capture")

    def get_system_prompt(self) -> str:
        return """You are a data capture agent for an AI concierge platform.

Your role is to identify and extract structured information from conversations including:
- Preferences (favorite restaurants, cuisines, activities)
- Important dates (birthdays, anniversaries, events)
- Family member names and relationships
- Addresses and contact information
- Dietary restrictions and allergies
- Interests and hobbies
- Communication preferences

OUTPUT FORMAT:
Return extracted information as structured JSON that can be stored in the database.

Example:
{
  "preferences": {
    "dining": {
      "favorite_cuisines": ["Italian", "Japanese"],
      "price_band": "$$$",
      "disliked_restaurants": ["Restaurant X"]
    }
  },
  "important_dates": [
    {
      "title": "John's Birthday",
      "date": "2024-03-15",
      "category": "Birthday"
    }
  ],
  "dietary_restrictions": ["Gluten-free", "No shellfish"]
}

Only extract information that is explicitly stated. Don't infer or guess.
"""

    def extract_from_conversation(self, conversation_text: str) -> dict:
        """
        Extract structured data from conversation text.
        Returns dictionary of extracted information.
        """
        # TODO: Implement extraction logic with Claude
        # TODO: Format response as structured JSON
        # TODO: Validate extracted data
        return {}
