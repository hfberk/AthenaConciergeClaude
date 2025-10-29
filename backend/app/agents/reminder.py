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
        date_item = None
        if reminder.get('date_item_id'):
            date_item = SupabaseQuery.get_by_id(
                client=self.db,
                table='date_items',
                id_column='date_item_id',
                id_value=reminder['date_item_id']
            )

        # Get person from comm_identity
        comm_identity = SupabaseQuery.get_by_id(
            client=self.db,
            table='comm_identities',
            id_column='comm_identity_id',
            id_value=reminder['comm_identity_id']
        )

        person = SupabaseQuery.get_by_id(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=comm_identity['person_id']
        )

        logger.info("Sending reminder",
                   person_id=str(person['person_id']),
                   date_item=date_item.get('title') if date_item else 'General reminder',
                   channel=comm_identity.get('channel_type'))

        # Build context for reminder
        from app.services.context_builder import ContextBuilder
        context_builder = ContextBuilder(self.db)
        context = context_builder.build_context(person['person_id'])

        # Generate reminder message using Claude
        if date_item:
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

            reminder_request = f"""Generate a reminder message for this important date:
- Title: {date_item.get('title')}
- Date: {date_item.get('next_occurrence') or date_item.get('date_value')}
- Category: {category_name}
- Notes: {date_item.get('notes') or 'None'}

Use the client's context to personalize the reminder and suggest helpful next steps.
"""
        else:
            # Generic reminder (created via reminder management)
            action = reminder.get('metadata_jsonb', {}).get('action', 'your reminder')
            reminder_request = f"""Generate a friendly reminder message:

Reminder: {action}

Use the client's context to personalize this reminder. Keep it concise and helpful.
"""

        reminder_message = self.execute(reminder_request, context)

        # Send via ProactiveMessagingService
        from app.services.proactive_messaging import ProactiveMessagingService
        messaging_service = ProactiveMessagingService(self.db)

        try:
            messaging_service.send_to_person(
                person_id=person['person_id'],
                message_text=reminder_message,
                agent_name='reminder',
                channel_type=comm_identity.get('channel_type'),
                subject='Reminder' if date_item else None
            )

            # Mark reminder as sent
            SupabaseQuery.update(
                client=self.db,
                table='reminder_rules',
                id_column='reminder_rule_id',
                id_value=reminder['reminder_rule_id'],
                data={'sent_at': datetime.utcnow().isoformat()}
            )

            logger.info("Reminder sent successfully",
                       person_id=str(person['person_id']),
                       reminder_id=str(reminder['reminder_rule_id']))

        except Exception as e:
            logger.error("Failed to send reminder",
                        reminder_id=str(reminder['reminder_rule_id']),
                        error=str(e),
                        exc_info=True)
            # Don't mark as sent if delivery failed
            raise
