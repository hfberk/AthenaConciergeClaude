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
- Be warm but professional and concise
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
                   person_id=str(person['person_id']),
                   conversation_id=str(conversation['conversation_id']))

        # Determine intent and route to specialized agent if appropriate
        intent = self._determine_intent(user_message)

        logger.info("Detected intent",
                   intent=intent,
                   message_preview=user_message[:50])

        # Route to specialized agents based on intent
        if intent == "reminder_create":
            from app.agents.reminder_management import ReminderManagementAgent
            reminder_agent = ReminderManagementAgent(self.db)
            response = reminder_agent.process_reminder_request(
                user_message=user_message,
                person=person,
                conversation=conversation,
                context=context
            )
        elif intent == "reminder_list":
            from app.agents.reminder_management import ReminderManagementAgent
            reminder_agent = ReminderManagementAgent(self.db)
            response = reminder_agent.list_reminders(person=person)
        elif intent == "recommendation":
            from app.agents.recommendation import RecommendationAgent
            recommendation_agent = RecommendationAgent(self.db)
            response = recommendation_agent.recommend(user_message, context)
        elif intent == "project_management":
            from app.agents.project_management import ProjectManagementAgent
            project_agent = ProjectManagementAgent(self.db)
            # For now, use execute method; can be enhanced with specific methods
            response = project_agent.execute(user_message, context)
        else:
            # General intent - orchestrator handles directly
            response = self.execute(user_message, context)

        return response

    def _determine_intent(self, user_message: str) -> str:
        """
        Analyze user message to determine intent.
        Routes to specialized agents based on detected intent.
        """
        message_lower = user_message.lower()

        # Reminder intents (high priority - check first)
        reminder_create_keywords = ["remind me", "set a reminder", "reminder for", "don't forget", "remember to"]
        reminder_list_keywords = ["show my reminders", "list reminders", "what reminders", "my reminders"]

        if any(keyword in message_lower for keyword in reminder_create_keywords):
            return "reminder_create"
        elif any(keyword in message_lower for keyword in reminder_list_keywords):
            return "reminder_list"

        # Other intents
        elif any(word in message_lower for word in ["recommend", "suggest", "find me", "looking for"]):
            return "recommendation"
        elif any(word in message_lower for word in ["project", "plan event", "organize", "help me plan"]):
            return "project_management"
        else:
            return "general"
