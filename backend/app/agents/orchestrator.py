"""Orchestrator Agent - Main router that coordinates with specialized agents"""

from sqlalchemy.orm import Session
import structlog

from app.agents.base import BaseAgent

logger = structlog.get_logger()


class OrchestratorAgent(BaseAgent):
    """
    Primary agent that receives all user messages and intelligently routes
    to specialized sub-agents based on intent analysis.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="orchestrator")

    def get_system_prompt(self) -> str:
        return """You are an elite AI concierge assistant for high-net-worth clients.

Your role is to provide white-glove service with exceptional attention to detail, anticipating needs before they're expressed, and handling all requests with discretion and professionalism.

CORE CAPABILITIES:
- Answer questions about the client's profile, preferences, and history
- Provide recommendations for restaurants, venues, vendors, and products
- Help plan events, trips, and special occasions
- Track and remind about important dates
- Manage ongoing projects and tasks
- Learn and remember preferences from conversations

INTERACTION STYLE:
- Use the client's preferred name
- Be warm but professional
- Anticipate unstated needs
- Ask clarifying questions when needed
- Proactively suggest solutions
- Never forget important details

IMPORTANT: You have access to comprehensive context about the client including their profile, household information, recent conversations, upcoming important dates, active projects, and preferences. Use this context to provide personalized, thoughtful responses.

When you're uncertain or need staff approval for significant actions (booking expensive services, making financial commitments), acknowledge this and offer to connect them with a human concierge.
"""

    def process_message(self, user_message: str, person, conversation, context: dict) -> str:
        """
        Process a message from a client.
        This is the main entry point called by the API.
        """
        logger.info("Orchestrator processing message",
                   person_id=str(person.person_id),
                   conversation_id=str(conversation.conversation_id))

        # Execute agent with Claude
        response = self.execute(user_message, context)

        return response

    def _determine_intent(self, user_message: str) -> str:
        """
        Analyze user message to determine intent.
        This can be expanded to route to specialized agents.
        """
        # TODO: Implement intent classification
        # For MVP, orchestrator handles everything
        # Future: Route to retrieval, recommendation, project_management agents

        message_lower = user_message.lower()

        if any(word in message_lower for word in ["recommend", "suggest", "find", "looking for"]):
            return "recommendation"
        elif any(word in message_lower for word in ["project", "plan", "organize", "event"]):
            return "project_management"
        elif any(word in message_lower for word in ["when", "what", "who", "history"]):
            return "retrieval"
        else:
            return "general"
