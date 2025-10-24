"""Reminder Management Agent - Handles user requests to create and manage reminders"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
import json
import structlog

from app.agents.base import BaseAgent
from app.utils.supabase_helpers import SupabaseQuery

logger = structlog.get_logger()


class ReminderManagementAgent(BaseAgent):
    """
    Manages user requests to create, update, list, and delete reminders.
    Uses Claude for natural language parsing of reminder requests.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="reminder_management")

    def get_system_prompt(self) -> str:
        return """You are a reminder management agent for an AI concierge platform.

Your role is to help users create, manage, and track reminders through natural language.

CAPABILITIES:
1. Parse natural language reminder requests
2. Extract key information: what, when, recurrence
3. Create reminder rules in the system
4. List existing reminders
5. Update or cancel reminders

PARSING GUIDELINES:
When a user asks for a reminder, extract:
- **action**: What to remind about (e.g., "call John", "birthday party planning")
- **datetime**: When to send the reminder (ISO format with timezone)
- **recurrence**: If it's recurring (daily, weekly, monthly, yearly)
- **advance_notice**: How far in advance (e.g., "2 days before", "1 week before")

RESPONSE FORMAT:
When parsing a reminder request, respond with a JSON object:
```json
{
  "action": "parsed_action",
  "reminder_type": "scheduled",
  "scheduled_datetime": "2025-10-25T15:00:00+00:00",
  "date_item_title": "Optional: if this is about an existing date/event",
  "notes": "Additional context",
  "needs_clarification": false,
  "clarification_question": "Optional: if you need more info"
}
```

For recurring reminders or date-based reminders:
```json
{
  "action": "parsed_action",
  "reminder_type": "lead_time",
  "lead_time_days": 7,
  "date_item_title": "John's Birthday",
  "create_date_item": true,
  "date_value": "2025-03-15",
  "notes": "Additional context"
}
```

IMPORTANT:
- If the request is ambiguous, set needs_clarification=true and ask a clear question
- Parse relative times ("tomorrow", "next week", "in 2 hours") into absolute datetimes
- Use the context to understand references ("his birthday" -> look in context for whose)
- Be conversational and friendly in confirmations
- Current datetime is provided in context

EXAMPLES:
User: "Remind me to call John tomorrow at 3pm"
→ Parse: action="Call John", scheduled_datetime="2025-10-25T15:00:00+00:00"

User: "Set a reminder for Mom's birthday 2 weeks before"
→ Parse: Create date_item if not exists, reminder_type="lead_time", lead_time_days=14

User: "Remind me in 30 minutes"
→ Parse: action="Check in", scheduled_datetime=now+30min

User: "Remind me about that thing"
→ needs_clarification=true, ask "What would you like to be reminded about?"
"""

    def process_reminder_request(
        self,
        user_message: str,
        person: dict,
        conversation: dict,
        context: dict
    ) -> str:
        """
        Process a user's reminder request and create the reminder.

        Args:
            user_message: The user's reminder request
            person: Person record from database
            conversation: Conversation record
            context: Full context from ContextBuilder

        Returns:
            str: Response to user confirming reminder creation or asking for clarification
        """
        logger.info(
            "Processing reminder request",
            person_id=str(person['person_id']),
            message=user_message
        )

        # Add current datetime to context for parsing relative times
        enhanced_context = {
            **context,
            "current_datetime": datetime.utcnow().isoformat(),
            "timezone": person.get('timezone', 'UTC')
        }

        # Use Claude to parse the reminder request
        parse_prompt = f"""Parse this reminder request and extract the structured information:

"{user_message}"

Respond with ONLY the JSON object as specified in the system prompt. No additional text."""

        try:
            response = self.execute(parse_prompt, enhanced_context)

            # Parse JSON response
            # Claude sometimes wraps JSON in ```json blocks, so clean it
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            parsed = json.loads(response_clean)

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Claude response as JSON",
                error=str(e),
                response=response
            )
            return "I had trouble understanding that reminder request. Could you please rephrase it? For example: 'Remind me to call Sarah tomorrow at 2pm'"

        # Check if clarification is needed
        if parsed.get('needs_clarification'):
            clarification = parsed.get('clarification_question',
                "Could you provide more details about when you'd like to be reminded?")
            return clarification

        # Create the reminder
        try:
            reminder_confirmation = self._create_reminder(
                person=person,
                parsed_data=parsed,
                context=context
            )
            return reminder_confirmation

        except Exception as e:
            logger.error(
                "Failed to create reminder",
                person_id=str(person['person_id']),
                error=str(e),
                exc_info=True
            )
            return "I encountered an error while setting up your reminder. Please try again or contact support if the issue persists."

    def _create_reminder(
        self,
        person: dict,
        parsed_data: dict,
        context: dict
    ) -> str:
        """
        Create a reminder rule in the database based on parsed data.

        Returns:
            str: Confirmation message to user
        """
        reminder_type = parsed_data.get('reminder_type', 'scheduled')
        action = parsed_data.get('action', 'Reminder')

        # Get or create date_item if this is about a specific date
        date_item_id = None
        if parsed_data.get('create_date_item') or parsed_data.get('date_item_title'):
            date_item_id = self._get_or_create_date_item(
                person=person,
                title=parsed_data.get('date_item_title', action),
                date_value=parsed_data.get('date_value'),
                notes=parsed_data.get('notes')
            )

        # Get user's primary comm_identity (for Slack)
        comm_identities = SupabaseQuery.select_active(
            client=self.db,
            table='comm_identities',
            filters={
                'person_id': person['person_id'],
                'is_primary': True
            },
            limit=1
        )

        if not comm_identities:
            # Fallback: any comm_identity
            comm_identities = SupabaseQuery.select_active(
                client=self.db,
                table='comm_identities',
                filters={'person_id': person['person_id']},
                limit=1
            )

        if not comm_identities:
            raise ValueError(f"No comm_identity found for person {person['person_id']}")

        comm_identity = comm_identities[0]

        # Create reminder_rule
        reminder_data = {
            'reminder_rule_id': str(uuid4()),
            'org_id': person['org_id'],
            'date_item_id': date_item_id,
            'comm_identity_id': comm_identity['comm_identity_id'],
            'reminder_type': reminder_type,
            'metadata_jsonb': {
                'action': action,
                'user_request': parsed_data,
                'created_by': 'reminder_management_agent'
            },
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Add type-specific fields
        if reminder_type == 'scheduled':
            reminder_data['scheduled_datetime'] = parsed_data['scheduled_datetime']
        elif reminder_type == 'lead_time':
            reminder_data['lead_time_days'] = parsed_data.get('lead_time_days', 7)
            # Calculate scheduled_datetime based on date_item and lead_time
            if date_item_id:
                date_item = SupabaseQuery.get_by_id(
                    client=self.db,
                    table='date_items',
                    id_column='date_item_id',
                    id_value=date_item_id
                )
                if date_item and date_item.get('next_occurrence'):
                    target_date = datetime.fromisoformat(date_item['next_occurrence'])
                    reminder_date = target_date - timedelta(days=reminder_data['lead_time_days'])
                    reminder_data['scheduled_datetime'] = reminder_date.isoformat()

        reminder = SupabaseQuery.insert(self.db, 'reminder_rules', reminder_data)

        logger.info(
            "Created reminder rule",
            reminder_id=str(reminder['reminder_rule_id']),
            person_id=str(person['person_id']),
            reminder_type=reminder_type
        )

        # Generate confirmation message
        return self._generate_confirmation(parsed_data, reminder_data)

    def _get_or_create_date_item(
        self,
        person: dict,
        title: str,
        date_value: str = None,
        notes: str = None
    ) -> str:
        """
        Get existing or create new date_item.

        Returns:
            str: date_item_id
        """
        # Look for existing date_item with same title
        date_items = SupabaseQuery.select_active(
            client=self.db,
            table='date_items',
            filters={
                'person_id': person['person_id'],
                'title': title
            },
            limit=1
        )

        if date_items:
            logger.debug(
                "Found existing date_item",
                date_item_id=date_items[0]['date_item_id']
            )
            return date_items[0]['date_item_id']

        # Create new date_item
        # Get default category or create one
        categories = SupabaseQuery.select_active(
            client=self.db,
            table='date_categories',
            filters={'org_id': person['org_id']},
            limit=1
        )

        if not categories:
            # Create default category
            category_data = {
                'date_category_id': str(uuid4()),
                'org_id': person['org_id'],
                'category_name': 'General',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            category = SupabaseQuery.insert(self.db, 'date_categories', category_data)
        else:
            category = categories[0]

        # Create date_item
        date_item_data = {
            'date_item_id': str(uuid4()),
            'org_id': person['org_id'],
            'person_id': person['person_id'],
            'date_category_id': category['date_category_id'],
            'title': title,
            'date_value': date_value or datetime.utcnow().date().isoformat(),
            'next_occurrence': date_value,
            'notes': notes,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        date_item = SupabaseQuery.insert(self.db, 'date_items', date_item_data)

        logger.info(
            "Created date_item",
            date_item_id=str(date_item['date_item_id']),
            title=title
        )

        return date_item['date_item_id']

    def _generate_confirmation(self, parsed_data: dict, reminder_data: dict) -> str:
        """Generate a friendly confirmation message"""
        action = parsed_data.get('action', 'your reminder')

        if reminder_data.get('scheduled_datetime'):
            # Format datetime in friendly way
            dt = datetime.fromisoformat(reminder_data['scheduled_datetime'].replace('Z', '+00:00'))
            time_str = dt.strftime('%B %d at %I:%M %p')
            return f"Got it! I'll remind you to {action} on {time_str}."
        elif reminder_data.get('lead_time_days'):
            days = reminder_data['lead_time_days']
            return f"Perfect! I'll remind you about {action} {days} days in advance."
        else:
            return f"Reminder set! I'll remind you to {action}."

    def list_reminders(self, person: dict) -> str:
        """List all pending reminders for a person"""
        # Get all reminder_rules that haven't been sent yet
        all_reminders = SupabaseQuery.select_active(
            client=self.db,
            table='reminder_rules'
        )

        # Filter for this person's reminders that haven't been sent
        pending_reminders = []
        for reminder in all_reminders:
            # Get associated comm_identity to check person
            comm_identity = SupabaseQuery.get_by_id(
                client=self.db,
                table='comm_identities',
                id_column='comm_identity_id',
                id_value=reminder['comm_identity_id']
            )

            if (comm_identity and
                comm_identity['person_id'] == person['person_id'] and
                not reminder.get('sent_at')):
                pending_reminders.append(reminder)

        if not pending_reminders:
            return "You don't have any pending reminders."

        # Format reminder list
        reminder_list = ["Here are your pending reminders:\n"]
        for i, reminder in enumerate(pending_reminders, 1):
            action = reminder.get('metadata_jsonb', {}).get('action', 'Reminder')
            scheduled = reminder.get('scheduled_datetime')
            if scheduled:
                dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
                time_str = dt.strftime('%B %d at %I:%M %p')
                reminder_list.append(f"{i}. {action} - {time_str}")
            else:
                reminder_list.append(f"{i}. {action}")

        return "\n".join(reminder_list)
