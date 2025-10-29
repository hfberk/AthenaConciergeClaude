"""Proactive Agent - Generates and sends unsolicited but helpful recommendations"""

from supabase import Client
from datetime import datetime, timedelta
import structlog

from app.agents.base import BaseAgent
from app.utils.supabase_helpers import SupabaseQuery
from app.services.context_builder import ContextBuilder
from app.services.proactive_messaging import ProactiveMessagingService

logger = structlog.get_logger()


class ProactiveAgent(BaseAgent):
    """
    Scans for opportunities to send helpful proactive messages.
    Respects user preferences for frequency and timing.
    """

    def __init__(self, db: Client):
        super().__init__(db, agent_name="proactive")

    def get_system_prompt(self) -> str:
        return """You are a proactive assistant for an AI concierge platform.

Your role is to identify opportunities to be helpful BEFORE the client asks.

PROACTIVE OPPORTUNITIES:
1. **Upcoming dates without plans** - Important date in 1-4 weeks with no associated project
2. **Stale projects** - Project not updated in 3+ days that's marked in_progress
3. **Seasonal suggestions** - Relevant recommendations based on time of year
4. **Follow-up opportunities** - Past conversations that may need follow-up

MESSAGING GUIDELINES:
- Be genuinely helpful, not intrusive
- Provide actionable suggestions with specific next steps
- Reference past conversations and preferences
- Keep messages concise (2-3 sentences)
- Always offer to help more if they're interested
- Respect the client's time and attention

FREQUENCY CHECK:
Before generating a message, check:
- When was the last proactive message sent to this client?
- What is their preferred frequency? (daily, weekly, off)
- Don't send if one was sent within their frequency window

OUTPUT:
If you find a proactive opportunity, respond with:
```json
{
  "should_send": true,
  "message": "Your concise, helpful proactive message here",
  "opportunity_type": "upcoming_date" | "stale_project" | "seasonal" | "follow_up",
  "reasoning": "Brief internal note on why this is helpful"
}
```

If no opportunity or too soon since last message:
```json
{
  "should_send": false,
  "reasoning": "Why we're not sending (e.g., sent recently, no clear opportunities)"
}
```

EXAMPLE:
```json
{
  "should_send": true,
  "message": "Hi Sarah! I noticed John's birthday is coming up in 2 weeks. Last year you mentioned he loved that private dinner at The Modern. Would you like help planning something special this year?",
  "opportunity_type": "upcoming_date",
  "reasoning": "Birthday in 2 weeks, no plans started, strong preference signal from last year"
}
```
"""

    def scan_and_send_proactive_messages(self):
        """
        Main scheduled task that scans all active users for proactive opportunities.
        """
        logger.info("Starting proactive message scan")

        # Get all active persons
        persons = SupabaseQuery.select_active(
            client=self.db,
            table='persons',
            filters={'person_type': 'client'}
        )

        messages_sent = 0
        for person in persons:
            try:
                sent = self._check_and_send_proactive(person)
                if sent:
                    messages_sent += 1
            except Exception as e:
                logger.error(
                    "Error processing proactive message for person",
                    person_id=str(person['person_id']),
                    error=str(e),
                    exc_info=True
                )

        logger.info(
            "Proactive message scan completed",
            total_persons=len(persons),
            messages_sent=messages_sent
        )

    def _check_and_send_proactive(self, person: dict) -> bool:
        """
        Check if we should send a proactive message to this person.

        Returns:
            bool: True if message was sent, False otherwise
        """
        person_id = person['person_id']

        # Get user preferences
        metadata = person.get('metadata_jsonb', {})
        proactive_prefs = metadata.get('proactive_preferences', {})

        # Check if proactive messages are enabled
        frequency = proactive_prefs.get('frequency', 'daily')  # default: daily
        if frequency == 'off':
            logger.debug(
                "Proactive messages disabled for user",
                person_id=str(person_id)
            )
            return False

        # Check when last proactive message was sent
        last_sent = proactive_prefs.get('last_proactive_sent')
        if last_sent:
            last_sent_dt = datetime.fromisoformat(last_sent.replace('Z', '+00:00'))
            now = datetime.utcnow()

            # Determine frequency window
            if frequency == 'daily':
                window = timedelta(hours=20)  # Once per day, with 4-hour buffer
            elif frequency == 'weekly':
                window = timedelta(days=6)  # Once per week, with 1-day buffer
            else:
                window = timedelta(hours=20)  # Default to daily

            if now - last_sent_dt < window:
                logger.debug(
                    "Too soon since last proactive message",
                    person_id=str(person_id),
                    last_sent=last_sent,
                    frequency=frequency
                )
                return False

        # If no preference set yet, ask user first
        if 'frequency' not in proactive_prefs:
            logger.info(
                "No proactive preference set, asking user",
                person_id=str(person_id)
            )
            return self._ask_proactive_preference(person)

        # Build context and look for opportunities
        context_builder = ContextBuilder(self.db)
        context = context_builder.build_context(person_id)

        # Use Claude to analyze context and determine if we should send
        analysis_prompt = """Analyze this client's context and determine if there's a good proactive opportunity.

Consider:
1. Upcoming dates in next 1-4 weeks without associated projects
2. Projects that haven't been updated in 3+ days
3. Patterns from recent conversations that suggest helpful follow-up
4. Seasonal or timely suggestions

Remember: Only suggest sending if it's genuinely helpful, not just to fill space.
"""

        response = self.execute(analysis_prompt, context)

        # Parse response
        import json
        try:
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            decision = json.loads(response_clean)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse proactive decision JSON",
                person_id=str(person_id),
                error=str(e),
                response=response
            )
            return False

        # If no opportunity found, don't send
        if not decision.get('should_send'):
            logger.debug(
                "No proactive opportunity found",
                person_id=str(person_id),
                reasoning=decision.get('reasoning')
            )
            return False

        # Send the proactive message
        message_text = decision.get('message')
        if not message_text:
            logger.warning(
                "Decision to send but no message provided",
                person_id=str(person_id)
            )
            return False

        try:
            messaging_service = ProactiveMessagingService(self.db)
            messaging_service.send_to_person(
                person_id=person_id,
                message_text=message_text,
                agent_name='proactive',
                channel_type='slack',  # Default to Slack for now
                subject='Helpful Suggestion'
            )

            # Update last_proactive_sent in user metadata
            self._update_last_sent(person, datetime.utcnow().isoformat())

            logger.info(
                "Sent proactive message",
                person_id=str(person_id),
                opportunity_type=decision.get('opportunity_type')
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to send proactive message",
                person_id=str(person_id),
                error=str(e),
                exc_info=True
            )
            return False

    def _ask_proactive_preference(self, person: dict) -> bool:
        """
        Ask user about their proactive message preferences.

        Returns:
            bool: True if preference question was sent
        """
        person_id = person['person_id']

        # Send message asking about preferences
        preference_message = """Hi! I'd love to send you helpful suggestions and reminders proactively (like upcoming events you might want to plan for).

How often would you like to receive these proactive messages?
- **Daily**: I'll check in once a day with helpful suggestions
- **Weekly**: I'll send suggestions once a week
- **Off**: Only respond when you message me (no proactive messages)

Just reply with "daily", "weekly", or "off" and I'll remember your preference!"""

        try:
            messaging_service = ProactiveMessagingService(self.db)
            messaging_service.send_to_person(
                person_id=person_id,
                message_text=preference_message,
                agent_name='proactive',
                channel_type='slack',
                subject='Proactive Message Preferences'
            )

            # Set a temporary preference to avoid asking again immediately
            metadata = person.get('metadata_jsonb', {})
            proactive_prefs = metadata.get('proactive_preferences', {})
            proactive_prefs['preference_asked_at'] = datetime.utcnow().isoformat()
            proactive_prefs['frequency'] = 'daily'  # Set default while waiting for response
            metadata['proactive_preferences'] = proactive_prefs

            SupabaseQuery.update(
                client=self.db,
                table='persons',
                id_column='person_id',
                id_value=person_id,
                data={'metadata_jsonb': metadata}
            )

            logger.info(
                "Asked user about proactive preferences",
                person_id=str(person_id)
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to ask about proactive preferences",
                person_id=str(person_id),
                error=str(e),
                exc_info=True
            )
            return False

    def _update_last_sent(self, person: dict, timestamp: str):
        """Update the last_proactive_sent timestamp in person metadata"""
        metadata = person.get('metadata_jsonb', {})
        proactive_prefs = metadata.get('proactive_preferences', {})
        proactive_prefs['last_proactive_sent'] = timestamp
        metadata['proactive_preferences'] = proactive_prefs

        SupabaseQuery.update(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=person['person_id'],
            data={'metadata_jsonb': metadata}
        )
