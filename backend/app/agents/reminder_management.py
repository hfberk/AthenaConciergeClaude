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
- **action**: What to remind about (e.g., "call John", "your dentist appointment")
- **scheduled_datetime**: When to SEND the reminder (ISO format with timezone)
- **recurrence**: If it's recurring (daily, weekly, monthly, yearly)
- **advance_notice**: How far in advance (e.g., "2 days before", "1 week before")

CRITICAL - HANDLING MULTIPLE TIME REFERENCES:
Users may mention multiple times in one request. You must determine which time is for SENDING the reminder:
- "Remind me in 5 minutes about my dentist appointment tomorrow"
  → scheduled_datetime = now + 5 minutes (when to SEND reminder)
  → action = "your dentist appointment tomorrow" (what to remind about)
  → The word "tomorrow" describes the event, NOT when to send the reminder
- "Remind me tomorrow about the party next week"
  → scheduled_datetime = tomorrow (when to SEND reminder)
  → action = "the party next week" (what to remind about)

CALCULATING RELATIVE TIMES - STEP BY STEP:
You will receive current_datetime in the context as an ISO format string with timezone.

CRITICAL: You MUST use the EXACT date, time, AND TIMEZONE from current_datetime as your starting point!
- current_datetime format: "2025-10-24T14:30:00-04:00" (Eastern) or "2025-10-24T14:30:00-05:00" (Eastern DST)
- The date portion is: YYYY-MM-DD (e.g., 2025-10-24 means October 24, 2025)
- The time portion is: HH:MM:SS (e.g., 14:30:00 means 2:30 PM)
- The timezone portion is: ±HH:MM (e.g., -04:00 is Eastern Daylight Time)

Calculate absolute datetimes from relative phrases by adding time to current_datetime:

1. "in X minutes": Add X minutes to the TIME in current_datetime, keep same DATE and TIMEZONE
   Example: current_datetime = "2025-10-24T14:30:00-04:00", user says "in 5 minutes"
   Parse current: Date = 2025-10-24, Time = 14:30:00, TZ = -04:00
   Add 5 minutes: 14:30 + 5 = 14:35
   Return: "2025-10-24T14:35:00-04:00" (SAME DATE, SAME TIMEZONE)

2. "in X hours": Add X hours to the TIME in current_datetime, keep same TIMEZONE
   Example: current_datetime = "2025-10-24T14:30:00-04:00", user says "in 2 hours"
   Parse current: Date = 2025-10-24, Time = 14:30:00, TZ = -04:00
   Add 2 hours: 14:30 + 2h = 16:30 (if goes past midnight, increment date)
   Return: "2025-10-24T16:30:00-04:00" (SAME TIMEZONE: -04:00)

3. "tomorrow at X pm": Add 1 day to the DATE in current_datetime, use specified time, keep TIMEZONE
   Example: current_datetime = "2025-10-24T14:30:00-04:00", user says "tomorrow at 3pm"
   Parse current: Date = 2025-10-24, TZ = -04:00
   Tomorrow: 2025-10-24 + 1 day = 2025-10-25
   Time: 3pm = 15:00:00
   Return: "2025-10-25T15:00:00-04:00" (NEXT DATE, SAME TIMEZONE)

4. "in X days": Add X days to the DATE in current_datetime, keep same time and TIMEZONE
   Example: current_datetime = "2025-10-24T14:30:00-04:00", user says "in 3 days"
   Parse current: Date = 2025-10-24, Time = 14:30:00, TZ = -04:00
   Add 3 days: 2025-10-24 + 3 = 2025-10-27
   Return: "2025-10-27T14:30:00-04:00" (3 DAYS LATER, SAME TIMEZONE)

WARNING: Do NOT use today's calendar date from your training! ONLY use the date from current_datetime!
WARNING: ALWAYS preserve the timezone from current_datetime in your response!

IMPORTANT DATETIME FORMAT REQUIREMENTS:
- ALWAYS return datetime in ISO 8601 format: "YYYY-MM-DDTHH:MM:SS±HH:MM"
- Use the SAME timezone as the current_datetime provided (typically the user's local timezone)
- If current_datetime is "2025-10-24T14:30:00-04:00", your response must also use -04:00
- If current_datetime is "2025-10-24T14:30:00-05:00", your response must also use -05:00
- Use 24-hour format (15:00:00, not 3:00:00 PM)
- Perform the actual calculation - do NOT return relative strings like "in 5 minutes"
- If current_datetime has milliseconds (e.g., "2025-10-24T14:30:00.123456"), strip them in your output

RESPONSE FORMAT:
When parsing a reminder request, respond with a JSON object ONLY. No additional text before or after:
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
- ONLY return valid JSON. No explanations, no additional text
- If the request is ambiguous, set needs_clarification=true and ask a clear question
- Parse relative times ("tomorrow", "next week", "in 2 hours") into absolute datetimes using current_datetime from context
- Use the user's timezone from context for datetime calculations
- Use context to understand references ("his birthday" -> look in context for whose)
- Current datetime is provided in context as "current_datetime"
- User timezone is provided in context as "timezone"

EXAMPLES (assume current_datetime = "2025-10-24T14:30:00-04:00" for all examples, Eastern timezone):

User: "Remind me to call John tomorrow at 3pm"
Context: current_datetime = "2025-10-24T14:30:00-04:00"
→ {"action": "call John", "reminder_type": "scheduled", "scheduled_datetime": "2025-10-25T15:00:00-04:00"}

User: "Remind me in 5 minutes about my dentist appointment tomorrow"
Context: current_datetime = "2025-10-24T14:30:00-04:00"
Calculation: 14:30:00 + 5 minutes = 14:35:00
→ {"action": "your dentist appointment tomorrow", "reminder_type": "scheduled", "scheduled_datetime": "2025-10-24T14:35:00-04:00"}
(Note: "in 5 minutes" determines scheduled_datetime, "tomorrow" describes the event)

User: "Set a reminder for Mom's birthday 2 weeks before"
→ {"action": "Mom's birthday", "reminder_type": "lead_time", "lead_time_days": 14, "date_item_title": "Mom's Birthday", "create_date_item": true}

User: "Remind me in 30 minutes"
Context: current_datetime = "2025-10-24T14:30:00-04:00"
Calculation: 14:30:00 + 30 minutes = 15:00:00
→ {"action": "check in", "reminder_type": "scheduled", "scheduled_datetime": "2025-10-24T15:00:00-04:00"}

User: "Remind me in 2 hours"
Context: current_datetime = "2025-10-24T14:30:00-04:00"
Calculation: 14:30:00 + 2 hours = 16:30:00
→ {"action": "check in", "reminder_type": "scheduled", "scheduled_datetime": "2025-10-24T16:30:00-04:00"}

User: "Remind me about that thing"
→ {"needs_clarification": true, "clarification_question": "What would you like to be reminded about, and when?"}
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

        # Get current datetime in user's timezone for parsing relative times
        import pytz
        user_tz_name = person.get('timezone', 'America/New_York')
        try:
            user_tz = pytz.timezone(user_tz_name)
            # Get current time in user's timezone
            current_dt_user_tz = datetime.now(user_tz)
            current_dt_str = current_dt_user_tz.isoformat()
        except Exception as e:
            logger.warning(
                "Failed to get user timezone, falling back to UTC",
                timezone=user_tz_name,
                error=str(e)
            )
            current_dt_str = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
            user_tz_name = 'UTC'

        # Add current datetime to context for parsing relative times
        enhanced_context = {
            **context,
            "current_datetime": current_dt_str,
            "timezone": user_tz_name
        }

        # Use Claude to parse the reminder request
        current_dt = enhanced_context.get('current_datetime')
        user_tz = enhanced_context.get('timezone', 'UTC')

        parse_prompt = f"""CURRENT CONTEXT:
- current_datetime: {current_dt}
- timezone: {user_tz}

Parse this reminder request and extract the structured information:

"{user_message}"

IMPORTANT: Use the current_datetime value above as your starting point for all relative time calculations.

Respond with ONLY the JSON object as specified in the system prompt. No additional text."""

        try:
            response = self.execute(parse_prompt, enhanced_context)

            # Log the raw response for debugging
            logger.info(
                "Raw Claude response for reminder parsing",
                raw_response=response,
                user_message=user_message,
                current_datetime=enhanced_context.get('current_datetime')
            )

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

            # Log the parsed result for debugging
            logger.info(
                "Successfully parsed reminder request",
                action=parsed.get('action'),
                reminder_type=parsed.get('reminder_type'),
                scheduled_datetime=parsed.get('scheduled_datetime'),
                user_message=user_message
            )

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Claude response as JSON",
                error=str(e),
                raw_response=response,
                cleaned_response=response_clean if 'response_clean' in locals() else None
            )
            return "I had trouble understanding that reminder request. Could you please rephrase it? For example: 'Remind me to call Sarah tomorrow at 2pm'"

        # Check if clarification is needed
        if parsed.get('needs_clarification'):
            clarification = parsed.get('clarification_question',
                "Could you provide more details about when you'd like to be reminded?")
            return clarification

        # Validate that scheduled reminders have a datetime
        if parsed.get('reminder_type') == 'scheduled':
            if not parsed.get('scheduled_datetime'):
                logger.error(
                    "Scheduled reminder missing scheduled_datetime field",
                    parsed_data=parsed,
                    user_message=user_message
                )
                return "I understood you want a reminder, but I couldn't determine when to send it. Could you specify the time? For example: 'in 10 minutes' or 'tomorrow at 3pm'"

            # Validate the datetime format and value
            validation_error = self._validate_datetime(parsed['scheduled_datetime'])
            if validation_error:
                logger.warning(
                    "Invalid datetime in parsed reminder",
                    datetime=parsed['scheduled_datetime'],
                    error=validation_error,
                    user_message=user_message
                )
                return f"I had trouble understanding the timing. {validation_error} Could you please specify when you'd like to be reminded? For example: 'in 10 minutes' or 'tomorrow at 3pm'"

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

    def _validate_datetime(self, scheduled_datetime: str) -> str:
        """
        Validate that the scheduled datetime makes sense.

        Returns:
            str: Error message if invalid, empty string if valid
        """
        # First, check if it looks like a datetime string
        if not scheduled_datetime or not isinstance(scheduled_datetime, str):
            logger.error(
                "Invalid scheduled_datetime type",
                scheduled_datetime=scheduled_datetime,
                type=type(scheduled_datetime).__name__
            )
            return "The time format is invalid (not a string)."

        # Check if it looks like a relative time expression instead of absolute
        relative_phrases = ["in ", "from now", "later", "minutes", "hours", "days"]
        if any(phrase in scheduled_datetime.lower() for phrase in relative_phrases):
            logger.error(
                "Received relative time expression instead of absolute datetime",
                scheduled_datetime=scheduled_datetime
            )
            return "The time must be in absolute format (YYYY-MM-DDTHH:MM:SS+00:00), not relative."

        try:
            # Try parsing with timezone
            dt = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))

            # Make 'now' timezone-aware for proper comparison
            from datetime import timezone
            now = datetime.now(timezone.utc)

            # Check if datetime is in the past (with 1 minute grace period for processing delays)
            grace_period = timedelta(minutes=1)
            if dt < now - grace_period:
                return "That time is in the past."

            # Check if datetime is too far in the future (more than 1 year)
            one_year = timedelta(days=365)
            if dt > now + one_year:
                return "That time is more than a year away. Please provide a date within the next year."

            return ""  # Valid

        except ValueError as e:
            logger.error(
                "Failed to parse datetime - invalid ISO format",
                scheduled_datetime=scheduled_datetime,
                error=str(e)
            )
            return "The time format is incorrect. Expected format: YYYY-MM-DDTHH:MM:SS+00:00"
        except Exception as e:
            logger.error(
                "Unexpected error validating datetime",
                scheduled_datetime=scheduled_datetime,
                error=str(e),
                exc_info=True
            )
            return "Unable to parse the time format."

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

            # Use timezone-aware datetime for comparison
            from datetime import timezone
            now = datetime.now(timezone.utc)

            # Calculate time difference for more natural language
            time_diff = dt - now

            # Format based on how soon the reminder is
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(time_diff.total_seconds() / 60)
                if minutes <= 1:
                    time_str = "in about a minute"
                else:
                    time_str = f"in {minutes} minutes"
            elif time_diff.total_seconds() < 86400:  # Less than 1 day
                hours = int(time_diff.total_seconds() / 3600)
                if hours == 1:
                    time_str = "in about an hour"
                else:
                    time_str = f"in {hours} hours"
            else:
                # For future dates, use the full date/time
                time_str = f"on {dt.strftime('%B %d at %I:%M %p')}"

            return f"Got it! I'll remind you about {action} {time_str}."
        elif reminder_data.get('lead_time_days'):
            days = reminder_data['lead_time_days']
            return f"Perfect! I'll remind you about {action} {days} days in advance."
        else:
            return f"Reminder set! I'll remind you about {action}."

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
