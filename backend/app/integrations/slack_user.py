"""Slack integration using User Token - Acts as Athena Concierge user"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import structlog
from slack_sdk import WebClient

from app.config import get_settings
from app.database import get_db_context
from app.agents.orchestrator import OrchestratorAgent
from app.services.context_builder import ContextBuilder
from app.utils.supabase_helpers import SupabaseQuery
from uuid import uuid4
from datetime import datetime

settings = get_settings()
logger = structlog.get_logger()


class SlackUserIntegration:
    """Handles Slack integration as a user (Athena Concierge)"""

    def __init__(self):
        if not settings.slack_user_token or not settings.slack_app_token:
            logger.warning("Slack user token or app token not configured, integration disabled")
            self.app = None
            self.user_client = None
            return

        # Create app with bot token for Socket Mode (required for Socket Mode)
        # but we'll use user token for sending messages
        if not settings.slack_bot_token:
            logger.error("Bot token required for Socket Mode even when using user token")
            self.app = None
            return

        self.app = App(token=settings.slack_bot_token)

        # Create separate client with USER token for sending messages as the user
        self.user_client = WebClient(token=settings.slack_user_token)

        # Get the user's ID
        try:
            auth_test = self.user_client.auth_test()
            self.user_id = auth_test['user_id']
            self.user_name = auth_test['user']
            logger.info("Slack user integration initialized",
                       user_id=self.user_id,
                       user_name=self.user_name)
        except Exception as e:
            logger.error("Failed to authenticate user token", error=str(e))
            self.app = None
            return

        self._register_handlers()

    # Blocked channels - ignore ALL events from these channels
    BLOCKED_CHANNELS = ["CBKLDP1A6"]

    def _is_blocked_channel(self, channel: str) -> bool:
        """Check if a channel is blocked"""
        return channel in self.BLOCKED_CHANNELS

    def _register_handlers(self):
        """Register Slack event handlers"""

        @self.app.event("message")
        def handle_message(event, say, client):
            """Handle messages in channels where Athena Concierge user is present"""
            try:
                # FIRST: Ignore ALL events from blocked channels
                if self._is_blocked_channel(event.get("channel")):
                    logger.debug(
                        "Ignoring message from blocked channel",
                        channel=event.get("channel")
                    )
                    return

                # Ignore message subtypes (edited, deleted, etc.) - only process new messages
                if event.get("subtype") is not None:
                    subtype = event.get("subtype")
                    logger.warning(
                        "DIAGNOSTIC: Filtering message with subtype - THIS MAY BE THE BUG",
                        subtype=subtype,
                        user=event.get("user"),
                        channel=event.get("channel"),
                        text_preview=event.get("text", "")[:100] if event.get("text") else None,
                        bot_id=event.get("bot_id"),
                        full_event_keys=list(event.keys())
                    )
                    return

                # Ignore messages from the Athena Concierge user itself to prevent loops
                if event.get("user") == self.user_id:
                    logger.info(
                        "DIAGNOSTIC: Filtering self-message (correct behavior)",
                        self_user_id=self.user_id,
                        channel=event.get("channel"),
                        text_preview=event.get("text", "")[:100] if event.get("text") else None
                    )
                    return

                # Ignore other bot messages
                if event.get("bot_id"):
                    logger.info(
                        "DIAGNOSTIC: Filtering bot message",
                        bot_id=event.get("bot_id"),
                        user=event.get("user"),
                        channel=event.get("channel")
                    )
                    return

                # Get message details
                user_id = event.get("user")
                text = event.get("text", "")
                channel = event.get("channel")

                # Slack channel ID conventions:
                # - DMs start with "D" (e.g., "D1234567890")
                # - Public channels start with "C"
                # - Private channels start with "G"
                is_dm = channel and channel.startswith("D")
                user_mentioned = f"<@{self.user_id}>" in text

                logger.info("Received Slack message for Athena Concierge",
                           user_id=user_id,
                           channel=channel,
                           is_dm=is_dm,
                           mentioned=user_mentioned,
                           has_text=bool(text))

                # Only respond to:
                # 1. Direct messages (DMs)
                # 2. Messages where Athena Concierge is @mentioned
                if not is_dm and not user_mentioned:
                    logger.info(
                        "DIAGNOSTIC: Ignoring message - not a DM and user not mentioned",
                        channel=channel,
                        is_dm=is_dm,
                        mentioned=user_mentioned,
                        text_preview=text[:100] if text else None
                    )
                    return

                # Remove the mention from the text if present
                clean_text = text.replace(f"<@{self.user_id}>", "").strip()

                logger.info(
                    "✅ DIAGNOSTIC: Message passed all filters - PROCESSING",
                    user_id=user_id,
                    channel=channel,
                    is_dm=is_dm,
                    text_preview=clean_text[:100]
                )

                # Look up or create person by Slack ID
                with get_db_context() as db:
                    # Query CommIdentity by Slack ID
                    comm_identities = SupabaseQuery.select_active(
                        client=db,
                        table='comm_identities',
                        filters={
                            'channel_type': 'slack',
                            'identity_value': user_id
                        },
                        limit=1
                    )
                    comm_identity = comm_identities[0] if comm_identities else None

                    # Auto-create user if not found
                    if not comm_identity:
                        logger.info("New Slack user detected, auto-creating", user_id=user_id)

                        # Get user info from Slack
                        try:
                            user_info = client.users_info(user=user_id)
                            slack_user = user_info.get("user", {})
                            display_name = slack_user.get("real_name") or slack_user.get("name") or f"Slack User {user_id}"
                            email = slack_user.get("profile", {}).get("email")
                        except Exception as e:
                            logger.warning("Could not fetch Slack user info", error=str(e))
                            display_name = f"Slack User {user_id}"
                            email = None

                        # Use default org (first org in database, or create one)
                        orgs = SupabaseQuery.select_active(
                            client=db,
                            table='organizations',
                            limit=1
                        )
                        default_org = orgs[0] if orgs else None

                        if not default_org:
                            # Create default organization
                            org_data = {
                                'org_id': str(uuid4()),
                                'name': 'Default Organization',
                                'settings_jsonb': {},
                                'created_at': datetime.utcnow().isoformat(),
                                'updated_at': datetime.utcnow().isoformat()
                            }
                            default_org = SupabaseQuery.insert(db, 'organizations', org_data)
                            logger.info("Created default organization", org_id=default_org['org_id'])

                        # Create person
                        person_data = {
                            'person_id': str(uuid4()),
                            'org_id': default_org['org_id'],
                            'person_type': 'client',
                            'full_name': display_name,
                            'preferred_name': display_name.split()[0] if display_name else 'there',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        person = SupabaseQuery.insert(db, 'persons', person_data)
                        logger.info("Created new person", person_id=person['person_id'])

                        # Create comm identity
                        comm_identity_data = {
                            'comm_identity_id': str(uuid4()),
                            'org_id': default_org['org_id'],
                            'person_id': person['person_id'],
                            'channel_type': 'slack',
                            'identity_value': user_id,
                            'is_primary': True,
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        comm_identity = SupabaseQuery.insert(db, 'comm_identities', comm_identity_data)
                        logger.info("Created Slack identity", comm_identity_id=comm_identity['comm_identity_id'])

                        # Create conversation for the new user
                        conversation_data = {
                            'conversation_id': str(uuid4()),
                            'org_id': person['org_id'],
                            'person_id': person['person_id'],
                            'channel_type': 'slack',
                            'external_thread_id': channel,
                            'status': 'active',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        conversation = SupabaseQuery.insert(db, 'conversations', conversation_data)
                        logger.info("Created conversation for new user", conversation_id=conversation['conversation_id'])

                        # Welcome message for new users (sent as Athena Concierge user)
                        welcome_msg = f"Hello {display_name.split()[0]}! Welcome to Athena Concierge. I'm here to assist you. How can I help you today?"
                        self._send_as_user(channel, welcome_msg)

                        # Save welcome message to conversation
                        welcome_msg_data = {
                            'message_id': str(uuid4()),
                            'org_id': person['org_id'],
                            'conversation_id': conversation['conversation_id'],
                            'direction': 'outbound',
                            'agent_name': 'system',
                            'content_text': welcome_msg,
                            'created_at': datetime.utcnow().isoformat()
                        }
                        SupabaseQuery.insert(db, 'messages', welcome_msg_data)

                        # Continue processing the first message instead of returning early
                        logger.info("Processing first message from new user")

                    # Fetch person from comm_identity
                    person = SupabaseQuery.get_by_id(
                        client=db,
                        table='persons',
                        id_column='person_id',
                        id_value=comm_identity['person_id']
                    )

                    # Get or create conversation
                    conversations = SupabaseQuery.select_active(
                        client=db,
                        table='conversations',
                        filters={
                            'person_id': person['person_id'],
                            'channel_type': 'slack',
                            'external_thread_id': channel
                        },
                        limit=1
                    )
                    conversation = conversations[0] if conversations else None

                    if conversation:
                        logger.info("Found existing conversation",
                                   conversation_id=conversation['conversation_id'],
                                   person_id=person['person_id'])
                    else:
                        logger.info("Creating new conversation",
                                   person_id=person['person_id'],
                                   channel=channel)
                        conversation_data = {
                            'conversation_id': str(uuid4()),
                            'org_id': person['org_id'],
                            'person_id': person['person_id'],
                            'channel_type': 'slack',
                            'external_thread_id': channel,
                            'status': 'active',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        conversation = SupabaseQuery.insert(db, 'conversations', conversation_data)

                    # Save inbound message
                    inbound_msg_data = {
                        'message_id': str(uuid4()),
                        'org_id': person['org_id'],
                        'conversation_id': conversation['conversation_id'],
                        'direction': 'inbound',
                        'sender_person_id': person['person_id'],
                        'content_text': clean_text,
                        'external_message_id': event.get('ts'),
                        'created_at': datetime.utcnow().isoformat()
                    }
                    inbound_msg = SupabaseQuery.insert(db, 'messages', inbound_msg_data)

                    # Build context and process with orchestrator
                    context_builder = ContextBuilder(db)
                    context = context_builder.build_context(person['person_id'], conversation['conversation_id'])

                    orchestrator = OrchestratorAgent(db)
                    ai_response = orchestrator.process_message(
                        user_message=clean_text,
                        person=person,
                        conversation=conversation,
                        context=context
                    )

                    # Save outbound message
                    outbound_msg_data = {
                        'message_id': str(uuid4()),
                        'org_id': person['org_id'],
                        'conversation_id': conversation['conversation_id'],
                        'direction': 'outbound',
                        'agent_name': 'orchestrator',
                        'content_text': ai_response,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    outbound_msg = SupabaseQuery.insert(db, 'messages', outbound_msg_data)

                    # Send response AS the Athena Concierge user
                    self._send_as_user(channel, ai_response)

                    logger.info("Sent response as Athena Concierge user",
                               channel=channel,
                               response_length=len(ai_response))

            except Exception as e:
                logger.error("Error handling Slack message",
                           error=str(e),
                           exc_info=True,
                           channel=event.get("channel"),
                           user_id=event.get("user"))
                # Send error message as the user
                try:
                    self._send_as_user(
                        event.get("channel"),
                        "I apologize, but I encountered an error processing your message. Please try again."
                    )
                except Exception as send_error:
                    logger.error("Failed to send error message to user",
                               error=str(send_error),
                               exc_info=True,
                               channel=event.get("channel"))

        @self.app.event("reaction_added")
        def handle_reaction_added(event, logger):
            """Handle reaction_added events - just ignore them for blocked channels"""
            try:
                # Ignore reactions from blocked channels
                if self._is_blocked_channel(event.get("item", {}).get("channel")):
                    logger.debug(
                        "Ignoring reaction from blocked channel",
                        channel=event.get("item", {}).get("channel")
                    )
                    return

                # For now, we don't process reactions - just acknowledge them
                logger.debug("Reaction added event received", event=event)

            except Exception as e:
                logger.error("Error handling reaction_added event",
                           error=str(e),
                           exc_info=True)

        @self.app.event("reaction_removed")
        def handle_reaction_removed(event, logger):
            """Handle reaction_removed events - just ignore them for blocked channels"""
            try:
                # Ignore reactions from blocked channels
                if self._is_blocked_channel(event.get("item", {}).get("channel")):
                    logger.debug(
                        "Ignoring reaction removal from blocked channel",
                        channel=event.get("item", {}).get("channel")
                    )
                    return

                # For now, we don't process reactions - just acknowledge them
                logger.debug("Reaction removed event received", event=event)

            except Exception as e:
                logger.error("Error handling reaction_removed event",
                           error=str(e),
                           exc_info=True)

    def _send_as_user(self, channel: str, text: str, thread_ts: str = None):
        """Send a message as the Athena Concierge user"""
        try:
            kwargs = {
                "channel": channel,
                "text": text,
                "as_user": True  # Important: Send as the authenticated user
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts

            response = self.user_client.chat_postMessage(**kwargs)
            return response
        except Exception as e:
            logger.error("Failed to send message as user", error=str(e), exc_info=True)
            raise

    def send_proactive_message(self, channel: str, text: str, thread_ts: str = None):
        """
        Public method for sending proactive messages as Athena Concierge user.
        Used by ProactiveMessagingService and agents for scheduled/proactive communication.

        Args:
            channel: Slack channel ID (DM or channel)
            text: Message text to send
            thread_ts: Optional thread timestamp for threaded replies

        Returns:
            Slack API response

        Raises:
            Exception: If message sending fails
        """
        if not self.user_client:
            raise RuntimeError("Slack user client not initialized")

        logger.info(
            "Sending proactive Slack message",
            channel=channel,
            message_length=len(text),
            is_threaded=bool(thread_ts)
        )

        return self._send_as_user(channel=channel, text=text, thread_ts=thread_ts)

    def get_dm_channel(self, slack_user_id: str) -> str:
        """
        Get or open a DM channel with a Slack user.

        Args:
            slack_user_id: Slack user ID (e.g., U1234567890)

        Returns:
            str: DM channel ID (e.g., D1234567890)

        Raises:
            Exception: If DM channel cannot be opened
        """
        if not self.user_client:
            raise RuntimeError("Slack user client not initialized")

        try:
            # Open DM channel (returns existing if already open)
            response = self.user_client.conversations_open(users=slack_user_id)

            if not response['ok']:
                raise RuntimeError(f"Failed to open DM channel: {response.get('error')}")

            dm_channel_id = response['channel']['id']
            logger.debug(
                "Opened Slack DM channel",
                slack_user_id=slack_user_id,
                dm_channel_id=dm_channel_id
            )

            return dm_channel_id

        except Exception as e:
            logger.error(
                "Failed to get Slack DM channel",
                slack_user_id=slack_user_id,
                error=str(e),
                exc_info=True
            )
            raise

    def start(self):
        """Start the Slack Socket Mode handler"""
        if not self.app:
            logger.warning("Slack app not initialized, skipping start")
            return

        handler = SocketModeHandler(self.app, settings.slack_app_token)
        logger.info("Starting Slack Socket Mode handler (User mode)")
        handler.start()


# Create singleton instance
slack_user_integration = SlackUserIntegration()


def start_slack_user_integration():
    """Entry point to start Slack user integration"""
    slack_user_integration.start()


if __name__ == "__main__":
    start_slack_user_integration()
