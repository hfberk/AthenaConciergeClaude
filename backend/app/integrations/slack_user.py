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

    def _register_handlers(self):
        """Register Slack event handlers"""

        @self.app.event("message")
        def handle_message(event, say, client):
            """Handle messages in channels where Athena Concierge user is present"""
            try:
                # Ignore messages from the Athena Concierge user itself to prevent loops
                if event.get("user") == self.user_id:
                    logger.debug("Ignoring message from Athena Concierge user itself")
                    return

                # Ignore other bot messages
                if event.get("bot_id"):
                    logger.debug("Ignoring bot message")
                    return

                # Get message details
                user_id = event.get("user")
                text = event.get("text", "")
                channel = event.get("channel")
                channel_type = event.get("channel_type", "")

                # Only respond to:
                # 1. Direct messages (DMs)
                # 2. Messages where Athena Concierge is @mentioned
                is_dm = channel_type == "im"
                user_mentioned = f"<@{self.user_id}>" in text

                if not is_dm and not user_mentioned:
                    logger.debug("Ignoring message - not a DM and user not mentioned")
                    return

                # Remove the mention from the text if present
                clean_text = text.replace(f"<@{self.user_id}>", "").strip()

                logger.info("Received Slack message for Athena Concierge",
                           user_id=user_id,
                           channel=channel,
                           is_dm=is_dm,
                           mentioned=user_mentioned)

                # Look up or create person by Slack ID
                with get_db_context() as db:
                    # Query CommIdentity by Slack ID
                    comm_identities = SupabaseQuery.select_active(
                        client=db,
                        table='comm_identities',
                        filters={
                            'channel': 'slack',
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
                                'id': str(uuid4()),
                                'name': 'Default Organization',
                                'settings': {},
                                'created_at': datetime.utcnow().isoformat(),
                                'updated_at': datetime.utcnow().isoformat()
                            }
                            default_org = SupabaseQuery.insert(db, 'organizations', org_data)
                            logger.info("Created default organization", org_id=default_org['id'])

                        # Create person
                        person_data = {
                            'id': str(uuid4()),
                            'org_id': default_org['id'],
                            'person_type': 'client',
                            'full_name': display_name,
                            'preferred_name': display_name.split()[0] if display_name else 'there',
                            'status': 'active',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        person = SupabaseQuery.insert(db, 'persons', person_data)
                        logger.info("Created new person", person_id=person['id'])

                        # Create comm identity
                        comm_identity_data = {
                            'id': str(uuid4()),
                            'org_id': default_org['id'],
                            'person_id': person['id'],
                            'channel': 'slack',
                            'identity_value': user_id,
                            'is_primary': True,
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
                        comm_identity = SupabaseQuery.insert(db, 'comm_identities', comm_identity_data)
                        logger.info("Created Slack identity", comm_identity_id=comm_identity['id'])

                        # Welcome message for new users (sent as Athena Concierge user)
                        welcome_msg = f"Hello {display_name.split()[0]}! Welcome to Athena Concierge. I'm here to assist you. How can I help you today?"
                        self._send_as_user(channel, welcome_msg)
                        return  # Don't process further, just send welcome

                    # Fetch person from comm_identity
                    person = SupabaseQuery.get_by_id(
                        client=db,
                        table='persons',
                        id_value=comm_identity['person_id']
                    )

                    # Get or create conversation
                    conversations = SupabaseQuery.select_active(
                        client=db,
                        table='conversations',
                        filters={
                            'channel': 'slack',
                            'external_thread_id': channel
                        },
                        limit=1
                    )
                    conversation = conversations[0] if conversations else None

                    if not conversation:
                        conversation_data = {
                            'id': str(uuid4()),
                            'org_id': person['org_id'],
                            'channel': 'slack',
                            'external_thread_id': channel,
                            'created_at': datetime.utcnow().isoformat()
                        }
                        conversation = SupabaseQuery.insert(db, 'conversations', conversation_data)

                    # Save inbound message
                    inbound_msg_data = {
                        'id': str(uuid4()),
                        'org_id': person['org_id'],
                        'conversation_id': conversation['id'],
                        'person_id': person['id'],
                        'channel': 'slack',
                        'direction': 'inbound',
                        'sender_type': 'person',
                        'body_text': clean_text,
                        'external_id': event.get('ts'),
                        'created_at': datetime.utcnow().isoformat()
                    }
                    inbound_msg = SupabaseQuery.insert(db, 'messages', inbound_msg_data)

                    # Build context and process with orchestrator
                    context_builder = ContextBuilder(db)
                    context = context_builder.build_context(person['id'], conversation['id'])

                    orchestrator = OrchestratorAgent(db)
                    ai_response = orchestrator.process_message(
                        user_message=clean_text,
                        person=person,
                        conversation=conversation,
                        context=context
                    )

                    # Save outbound message
                    outbound_msg_data = {
                        'id': str(uuid4()),
                        'org_id': person['org_id'],
                        'conversation_id': conversation['id'],
                        'channel': 'slack',
                        'direction': 'outbound',
                        'sender_type': 'agent',
                        'agent_name': 'orchestrator',
                        'body_text': ai_response,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    outbound_msg = SupabaseQuery.insert(db, 'messages', outbound_msg_data)

                    # Send response AS the Athena Concierge user
                    self._send_as_user(channel, ai_response, thread_ts=event.get("ts"))

                    logger.info("Sent response as Athena Concierge user",
                               channel=channel,
                               response_length=len(ai_response))

            except Exception as e:
                logger.error("Error handling Slack message", error=str(e), exc_info=True)
                # Send error message as the user
                try:
                    self._send_as_user(
                        event.get("channel"),
                        "I apologize, but I encountered an error processing your message. Please try again."
                    )
                except:
                    pass

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
