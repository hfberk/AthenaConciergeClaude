"""Base agent class with common functionality"""

from abc import ABC, abstractmethod
from uuid import uuid4
from datetime import datetime
from supabase import Client
from anthropic import Anthropic
import structlog

from app.config import get_settings
from app.utils.supabase_helpers import SupabaseQuery

settings = get_settings()
logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, db: Client, agent_name: str = None):
        self.db = db
        self.agent_name = agent_name or self.__class__.__name__
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self.max_tokens = settings.max_tokens

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass

    def execute(self, user_message: str, context: dict) -> str:
        """
        Execute the agent with a user message and context.
        This is the main entry point for agent execution.
        """
        run_id = uuid4()
        start_time = datetime.now()

        try:
            # Get system prompt
            system_prompt = self.get_system_prompt()

            # Build messages
            messages = self._build_messages(user_message, context)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )

            # Extract response text
            response_text = response.content[0].text

            # Log execution
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_execution(
                run_id=run_id,
                user_message=user_message,
                response=response_text,
                context=context,
                execution_time_ms=execution_time_ms,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )

            return response_text

        except Exception as e:
            logger.error("Agent execution failed",
                        agent=self.agent_name,
                        error=str(e),
                        run_id=str(run_id))
            raise

    def _build_messages(self, user_message: str, context: dict) -> list:
        """Build messages array for Claude API"""
        # Format context as a system message component
        context_text = self._format_context(context)

        messages = []

        # Add context as a user message if available
        if context_text:
            messages.append({
                "role": "user",
                "content": f"<context>\n{context_text}\n</context>"
            })
            messages.append({
                "role": "assistant",
                "content": "I've reviewed the context. I'm ready to help."
            })

        # Add actual user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    def _format_context(self, context: dict) -> str:
        """Format context dictionary into a readable string"""
        if not context:
            return ""

        parts = []

        # Person profile
        if context.get("person"):
            person = context["person"]
            parts.append(f"""
CLIENT PROFILE:
Name: {person.get('full_name')}
Preferred Name: {person.get('preferred_name')}
Type: {person.get('person_type')}
Timezone: {person.get('timezone')}
""")

        # Households
        if context.get("households"):
            parts.append("\nHOUSEHOLDS:")
            for household in context["households"]:
                parts.append(f"- {household.get('household_name')} ({household.get('household_type')})")

        # Recent conversations
        if context.get("recent_conversations"):
            parts.append("\nRECENT CONVERSATIONS:")
            for conv in context["recent_conversations"][:2]:  # Limit to most recent
                parts.append(f"\nConversation from {conv.get('updated_at', 'unknown')}:")
                for msg in conv.get("messages", [])[-3:]:  # Last 3 messages
                    parts.append(f"  [{msg['direction']}] {msg['content'][:100]}...")

        # Upcoming dates
        if context.get("upcoming_dates"):
            parts.append("\nUPCOMING IMPORTANT DATES:")
            for date in context["upcoming_dates"][:5]:  # Next 5 dates
                parts.append(f"- {date.get('title')} on {date.get('date')} ({date.get('category')})")

        # Active projects
        if context.get("active_projects"):
            parts.append("\nACTIVE PROJECTS:")
            for project in context["active_projects"]:
                parts.append(f"- {project.get('title')} (Status: {project.get('status')}, Priority: {project.get('priority')})")

        # Preferences
        if context.get("preferences"):
            prefs = context["preferences"]
            parts.append("\nPREFERENCES:")
            if prefs.get("interests"):
                parts.append(f"Interests: {', '.join(prefs['interests'])}")
            if prefs.get("dietary_restrictions"):
                parts.append(f"Dietary Restrictions: {', '.join(prefs['dietary_restrictions'])}")

        return "\n".join(parts)

    def _log_execution(self, run_id: uuid4, user_message: str, response: str,
                      context: dict, execution_time_ms: int, tokens_used: int):
        """Log agent execution to database"""
        try:
            # Find agent in roster
            agents = SupabaseQuery.select_active(
                client=self.db,
                table='agent_roster',
                filters={
                    'agent_name': self.agent_name,
                    'status': 'active'
                },
                limit=1
            )
            agent = agents[0] if agents else None

            if agent:
                log_data = {
                    'agent_execution_log_id': str(uuid4()),
                    'org_id': agent['org_id'],
                    'agent_id': agent['agent_id'],
                    'run_id': str(run_id),
                    'turn_index': 0,
                    'payload_jsonb': {
                        "user_message": user_message,
                        "response": response,
                        "context_summary": {
                            "person_id": context.get("person", {}).get("person_id"),
                            "has_conversations": bool(context.get("recent_conversations")),
                            "has_projects": bool(context.get("active_projects")),
                        }
                    },
                    'execution_time_ms': execution_time_ms,
                    'tokens_used': tokens_used,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                SupabaseQuery.insert(self.db, 'agent_execution_logs', log_data)
        except Exception as e:
            logger.warning("Failed to log agent execution", error=str(e))
