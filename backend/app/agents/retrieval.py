"""Retrieval Agent - Retrieves and synthesizes information from the database"""

from sqlalchemy.orm import Session
from app.agents.base import BaseAgent


class RetrievalAgent(BaseAgent):
    """
    Retrieves and synthesizes information from the database using SQL
    and semantic search.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="retrieval")

    def get_system_prompt(self) -> str:
        return """You are a specialized information retrieval agent for an AI concierge platform.

Your role is to accurately retrieve and synthesize information from the client's profile, conversation history, preferences, and past interactions.

CAPABILITIES:
- Answer factual questions about client profiles and preferences
- Retrieve conversation history and past interactions
- Find information about upcoming dates and events
- Provide project status updates
- Summarize preferences and patterns

Always cite specific dates, names, and details when available. If information is not in the context provided, clearly state that you don't have that information rather than guessing.
"""

    def retrieve(self, query: str, context: dict) -> str:
        """Retrieve information based on query"""
        return self.execute(query, context)
