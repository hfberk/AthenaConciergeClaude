"""Reminder Agent - Scheduled agent that generates and sends proactive reminders"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from app.agents.base import BaseAgent
from app.models.dates import ReminderRule, DateItem
from app.models.communication import CommIdentity, Message, Conversation

logger = structlog.get_logger()


class ReminderAgent(BaseAgent):
    """
    Scheduled execution agent that scans for pending reminders
    and generates contextual reminder messages.
    """

    def __init__(self, db: Session):
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

        now = datetime.utcnow()

        # Find reminders that should be sent
        pending_reminders = self.db.query(ReminderRule).filter(
            ReminderRule.sent_at.is_(None),
            ReminderRule.deleted_at.is_(None),
            ReminderRule.scheduled_datetime <= now
        ).all()

        logger.info(f"Found {len(pending_reminders)} pending reminders")

        for reminder in pending_reminders:
            try:
                self._send_reminder(reminder)
            except Exception as e:
                logger.error("Failed to send reminder",
                           reminder_id=str(reminder.reminder_rule_id),
                           error=str(e))

        logger.info("Reminder scan completed")

    def _send_reminder(self, reminder: ReminderRule):
        """Send a single reminder"""
        date_item = reminder.date_item
        person = date_item.person
        comm_identity = reminder.comm_identity

        logger.info("Sending reminder",
                   person_id=str(person.person_id),
                   date_item=date_item.title,
                   channel=comm_identity.channel_type)

        # Build context for reminder
        from app.services.context_builder import ContextBuilder
        context_builder = ContextBuilder(self.db)
        context = context_builder.build_context(person.person_id)

        # Generate reminder message
        reminder_request = f"""Generate a reminder message for this important date:
- Title: {date_item.title}
- Date: {date_item.next_occurrence or date_item.date_value}
- Category: {date_item.category.category_name if date_item.category else 'N/A'}
- Notes: {date_item.notes or 'None'}

Use the client's context to personalize the reminder and suggest helpful next steps.
"""

        reminder_message = self.execute(reminder_request, context)

        # Create or get conversation for reminders
        conversation = self.db.query(Conversation).filter(
            Conversation.person_id == person.person_id,
            Conversation.channel_type == comm_identity.channel_type,
            Conversation.subject == "Reminders",
            Conversation.deleted_at.is_(None)
        ).first()

        if not conversation:
            conversation = Conversation(
                org_id=person.org_id,
                person_id=person.person_id,
                channel_type=comm_identity.channel_type,
                subject="Reminders",
                status="active"
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        # Save message
        message = Message(
            org_id=person.org_id,
            conversation_id=conversation.conversation_id,
            direction="outbound",
            agent_name="reminder",
            content_text=reminder_message
        )
        self.db.add(message)

        # Mark reminder as sent
        reminder.sent_at = datetime.utcnow()

        self.db.commit()

        # TODO: Actually send via Slack/Email/SMS
        logger.info("Reminder sent successfully",
                   message_id=str(message.message_id))
