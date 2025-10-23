"""Reminder Agent - Scheduled agent that generates and sends proactive reminders"""

from supabase import Client
from datetime import datetime, timedelta
import structlog
from uuid import uuid4

from app.agents.base import BaseAgent
from app.utils.supabase_helpers import SupabaseQuery

logger = structlog.get_logger()


class ReminderAgent(BaseAgent):
    """
    Scheduled execution agent that scans for pending reminders
    and generates contextual reminder messages.
    """

    def __init__(self, db: Client):
        super().__init__(db, agent_name="reminder")

    def get_system_prompt(self) -> str:
        return """You are a reminder agent for an AI concierge platform.

Your role is to generate thoughtful, contextual reminder messages for important dates and events.

GUIDELINES:
- Reference the specific date and category
- Include relevant context from past conversations
- Suggest helpful next steps or planning assistance
- Be warm and proactive
- Keep reminders concise but personalized

Example: "Hi Sarah! Just a reminder that John's birthday is coming up on March 15th (2 weeks away). Last year you mentioned he loved that private dinner at The Modern. Would you like help planning something special this year?"
"""

    def scan_and_send_reminders(self):
        """
        Main scheduled task that scans for pending reminders
        and sends them via appropriate channels.
        """
        logger.info("Starting reminder scan")

        now = datetime.utcnow().isoformat()

        # Find reminders that should be sent
        # Note: Complex filtering (<=, IS NULL) needs custom query or fetch & filter
        all_reminders = SupabaseQuery.select_active(
            client=self.db,
            table='reminder_rules'
        )

        # Filter in Python for sent_at IS NULL and scheduled_datetime <= now
        pending_reminders = [
            r for r in all_reminders
            if r.get('sent_at') is None and r.get('scheduled_datetime') and r.get('scheduled_datetime') <= now
        ]

        logger.info(f"Found {len(pending_reminders)} pending reminders")

        for reminder in pending_reminders:
            try:
                self._send_reminder(reminder)
            except Exception as e:
                logger.error("Failed to send reminder",
                           reminder_id=str(reminder['reminder_rule_id']),
                           error=str(e))

        logger.info("Reminder scan completed")

    def _send_reminder(self, reminder: dict):
        """Send a single reminder"""
        # Fetch related entities
        date_item = SupabaseQuery.get_by_id(
            client=self.db,
            table='date_items',
            id_column='date_item_id',
            id_value=reminder['date_item_id']
        )

        person = SupabaseQuery.get_by_id(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=date_item['person_id']
        )

        comm_identity = SupabaseQuery.get_by_id(
            client=self.db,
            table='comm_identities',
            id_column='comm_identity_id',
            id_value=reminder['comm_identity_id']
        )

        logger.info("Sending reminder",
                   person_id=str(person['person_id']),
                   date_item=date_item.get('title'),
                   channel=comm_identity.get('channel_type'))

        # Build context for reminder
        from app.services.context_builder import ContextBuilder
        context_builder = ContextBuilder(self.db)
        context = context_builder.build_context(person['person_id'])

        # Fetch category if present
        category_name = 'N/A'
        if date_item.get('date_category_id'):
            category = SupabaseQuery.get_by_id(
                client=self.db,
                table='date_categories',
                id_column='date_category_id',
                id_value=date_item['date_category_id']
            )
            category_name = category.get('category_name') if category else 'N/A'

        # Generate reminder message
        reminder_request = f"""Generate a reminder message for this important date:
- Title: {date_item.get('title')}
- Date: {date_item.get('next_occurrence') or date_item.get('date_value')}
- Category: {category_name}
- Notes: {date_item.get('notes') or 'None'}

Use the client's context to personalize the reminder and suggest helpful next steps.
"""

        reminder_message = self.execute(reminder_request, context)

        # Create or get conversation for reminders
        conversations = SupabaseQuery.select_active(
            client=self.db,
            table='conversations',
            filters={
                'person_id': person['person_id'],
                'channel_type': comm_identity.get('channel_type'),
                'subject': 'Reminders'
            },
            limit=1
        )
        conversation = conversations[0] if conversations else None

        if not conversation:
            conversation_data = {
                'conversation_id': str(uuid4()),
                'org_id': person['org_id'],
                'person_id': person['person_id'],
                'channel_type': comm_identity.get('channel_type'),
                'subject': 'Reminders',
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            conversation = SupabaseQuery.insert(self.db, 'conversations', conversation_data)

        # Save message
        message_data = {
            'message_id': str(uuid4()),
            'org_id': person['org_id'],
            'conversation_id': conversation['conversation_id'],
            'direction': 'outbound',
            'agent_name': 'reminder',
            'content_text': reminder_message,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        message = SupabaseQuery.insert(self.db, 'messages', message_data)

        # Mark reminder as sent
        SupabaseQuery.update(
            client=self.db,
            table='reminder_rules',
            id_column='reminder_rule_id',
            id_value=reminder['reminder_rule_id'],
            data={'sent_at': datetime.utcnow().isoformat()}
        )

        # TODO: Actually send via Slack/Email/SMS
        logger.info("Reminder sent successfully",
                   message_id=str(message['message_id']))
