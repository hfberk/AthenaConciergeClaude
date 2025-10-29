"""Proactive Messaging Service - Centralized service for sending proactive messages"""

from uuid import uuid4, UUID
from datetime import datetime
from supabase import Client
import structlog

from app.utils.supabase_helpers import SupabaseQuery

logger = structlog.get_logger()


class ProactiveMessagingService:
    """
    Centralized service for sending proactive messages across all channels.
    Handles message persistence, channel routing, and delivery.
    """

    def __init__(self, db: Client):
        self.db = db

    def send_to_person(
        self,
        person_id: str | UUID,
        message_text: str,
        agent_name: str = "system",
        channel_type: str = "slack",
        subject: str = None
    ) -> dict:
        """
        Send a proactive message to a person via their preferred channel.

        Args:
            person_id: UUID of the person to message
            message_text: The message content to send
            agent_name: Name of the agent sending the message
            channel_type: Channel type (slack, email, sms)
            subject: Optional subject/conversation label

        Returns:
            dict: Message record that was created

        Raises:
            Exception: If person not found, no comm identity, or delivery fails
        """
        person_id_str = str(person_id)
        logger.info(
            "Sending proactive message",
            person_id=person_id_str,
            agent_name=agent_name,
            channel_type=channel_type
        )

        # Get person
        person = SupabaseQuery.get_by_id(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=person_id_str
        )

        if not person:
            raise ValueError(f"Person not found: {person_id_str}")

        # Get person's comm identity for the specified channel
        comm_identities = SupabaseQuery.select_active(
            client=self.db,
            table='comm_identities',
            filters={
                'person_id': person_id_str,
                'channel_type': channel_type
            },
            limit=1
        )

        if not comm_identities:
            raise ValueError(
                f"No {channel_type} identity found for person {person_id_str}"
            )

        comm_identity = comm_identities[0]

        # Get or create conversation for proactive messages
        conversation = self._get_or_create_conversation(
            person=person,
            channel_type=channel_type,
            identity_value=comm_identity['identity_value'],
            subject=subject
        )

        # Save message to database
        message_data = {
            'message_id': str(uuid4()),
            'org_id': person['org_id'],
            'conversation_id': conversation['conversation_id'],
            'direction': 'outbound',
            'agent_name': agent_name,
            'content_text': message_text,
            'created_at': datetime.utcnow().isoformat()
        }
        message = SupabaseQuery.insert(self.db, 'messages', message_data)

        # Send via appropriate channel
        if channel_type == 'slack':
            self._send_via_slack(
                identity_value=comm_identity['identity_value'],
                conversation=conversation,
                message_text=message_text
            )
        elif channel_type == 'email':
            self._send_via_email(
                identity_value=comm_identity['identity_value'],
                message_text=message_text,
                subject=subject or "Message from Athena Concierge"
            )
        elif channel_type == 'sms':
            self._send_via_sms(
                identity_value=comm_identity['identity_value'],
                message_text=message_text
            )
        else:
            logger.warning(
                f"Unsupported channel type: {channel_type}, message saved but not sent"
            )

        logger.info(
            "Proactive message sent successfully",
            message_id=str(message['message_id']),
            person_id=person_id_str,
            channel_type=channel_type
        )

        return message

    def _get_or_create_conversation(
        self,
        person: dict,
        channel_type: str,
        identity_value: str,
        subject: str = None
    ) -> dict:
        """Get existing conversation or create new one for proactive messages"""

        # For Slack, look up conversation by external_thread_id (the DM channel)
        # For other channels, look up by person_id and channel_type
        if channel_type == 'slack':
            # Get Slack DM channel ID
            dm_channel = self._get_slack_dm_channel(identity_value)

            # Find conversation by DM channel
            conversations = SupabaseQuery.select_active(
                client=self.db,
                table='conversations',
                filters={
                    'person_id': person['person_id'],
                    'channel_type': channel_type,
                    'external_thread_id': dm_channel
                },
                limit=1
            )
        else:
            # For email/sms, find by person and channel type
            conversations = SupabaseQuery.select_active(
                client=self.db,
                table='conversations',
                filters={
                    'person_id': person['person_id'],
                    'channel_type': channel_type
                },
                limit=1
            )

        if conversations:
            logger.debug(
                "Found existing conversation",
                conversation_id=conversations[0]['conversation_id']
            )
            return conversations[0]

        # Create new conversation
        conversation_data = {
            'conversation_id': str(uuid4()),
            'org_id': person['org_id'],
            'person_id': person['person_id'],
            'channel_type': channel_type,
            'external_thread_id': dm_channel if channel_type == 'slack' else None,
            'subject': subject or 'Athena Concierge',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        conversation = SupabaseQuery.insert(self.db, 'conversations', conversation_data)

        logger.info(
            "Created new conversation for proactive messaging",
            conversation_id=conversation['conversation_id'],
            person_id=person['person_id']
        )

        return conversation

    def _get_slack_dm_channel(self, slack_user_id: str) -> str:
        """
        Get or open a DM channel with a Slack user.

        Args:
            slack_user_id: Slack user ID (e.g., U1234567890)

        Returns:
            str: DM channel ID (e.g., D1234567890)
        """
        try:
            # Import here to avoid circular dependency
            from app.integrations.slack_user import slack_user_integration

            return slack_user_integration.get_dm_channel(slack_user_id)

        except Exception as e:
            logger.error(
                "Failed to get Slack DM channel",
                slack_user_id=slack_user_id,
                error=str(e),
                exc_info=True
            )
            raise

    def _send_via_slack(
        self,
        identity_value: str,
        conversation: dict,
        message_text: str
    ):
        """Send message via Slack"""
        try:
            # Import here to avoid circular dependency
            from app.integrations.slack_user import slack_user_integration

            # Get DM channel (should be in conversation's external_thread_id)
            dm_channel = conversation.get('external_thread_id')
            if not dm_channel:
                # Fallback: open DM channel
                dm_channel = self._get_slack_dm_channel(identity_value)

            # Send message as Athena Concierge user using public method
            slack_user_integration.send_proactive_message(
                channel=dm_channel,
                text=message_text
            )

            logger.debug(
                "Sent Slack message",
                channel=dm_channel,
                message_length=len(message_text)
            )

        except Exception as e:
            logger.error(
                "Failed to send Slack message",
                identity_value=identity_value,
                error=str(e),
                exc_info=True
            )
            raise

    def _send_via_email(self, identity_value: str, message_text: str, subject: str):
        """Send message via email (SES)"""
        try:
            from app.integrations.ses import send_email

            send_email(
                to_email=identity_value,
                subject=subject,
                body=message_text
            )

            logger.debug("Sent email message", to_email=identity_value)

        except Exception as e:
            logger.error(
                "Failed to send email message",
                identity_value=identity_value,
                error=str(e),
                exc_info=True
            )
            raise

    def _send_via_sms(self, identity_value: str, message_text: str):
        """Send message via SMS (future implementation)"""
        logger.warning(
            "SMS sending not yet implemented",
            phone_number=identity_value
        )
        # TODO: Implement SMS sending via Twilio or similar
        raise NotImplementedError("SMS sending not yet implemented")
