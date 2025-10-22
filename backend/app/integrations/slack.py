"""Slack integration using Socket Mode"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import structlog

from app.config import get_settings
from app.database import get_db_context
from app.agents.orchestrator import OrchestratorAgent
from app.services.context_builder import ContextBuilder

settings = get_settings()
logger = structlog.get_logger()


class SlackIntegration:
    """Handles Slack integration via Socket Mode"""

    def __init__(self):
        if not settings.slack_bot_token or not settings.slack_app_token:
            logger.warning("Slack credentials not configured, integration disabled")
            self.app = None
            return

        self.app = App(token=settings.slack_bot_token)
        self._register_handlers()

    def _register_handlers(self):
        """Register Slack event handlers"""

        @self.app.event("message")
        def handle_message(event, say, client):
            """Handle direct messages to the bot"""
            try:
                # Ignore bot messages
                if event.get("bot_id"):
                    return

                user_id = event.get("user")
                text = event.get("text")
                channel = event.get("channel")

                logger.info("Received Slack message",
                           user_id=user_id,
                           channel=channel)

                # Look up or create person by Slack ID
                with get_db_context() as db:
                    from app.models.communication import CommIdentity
                    from app.models.identity import Person
                    from uuid import UUID

                    comm_identity = db.query(CommIdentity).filter(
                        CommIdentity.channel_type == "slack",
                        CommIdentity.identity_value == user_id,
                        CommIdentity.deleted_at.is_(None)
                    ).first()

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
                        from app.models.identity import Organization
                        default_org = db.query(Organization).filter(
                            Organization.deleted_at.is_(None)
                        ).first()

                        if not default_org:
                            # Create default organization
                            default_org = Organization(
                                org_name="Default Organization",
                                org_type="concierge"
                            )
                            db.add(default_org)
                            db.commit()
                            db.refresh(default_org)
                            logger.info("Created default organization", org_id=str(default_org.org_id))

                        # Create person
                        person = Person(
                            org_id=default_org.org_id,
                            person_type="client",
                            full_name=display_name,
                            preferred_name=display_name.split()[0] if display_name else "there",
                            email=email
                        )
                        db.add(person)
                        db.commit()
                        db.refresh(person)
                        logger.info("Created new person", person_id=str(person.person_id))

                        # Create comm identity
                        comm_identity = CommIdentity(
                            org_id=default_org.org_id,
                            person_id=person.person_id,
                            channel_type="slack",
                            identity_value=user_id,
                            display_name=display_name
                        )
                        db.add(comm_identity)
                        db.commit()
                        db.refresh(comm_identity)
                        logger.info("Created Slack identity", comm_identity_id=str(comm_identity.comm_identity_id))

                        # Welcome message for new users
                        say(f"Hello {display_name.split()[0]}! 👋 Welcome to Athena Concierge. I'm your AI assistant. How can I help you today?")

                    person = comm_identity.person

                    # Get or create conversation
                    from app.models.communication import Conversation, Message

                    conversation = db.query(Conversation).filter(
                        Conversation.person_id == person.person_id,
                        Conversation.channel_type == "slack",
                        Conversation.external_thread_id == channel,
                        Conversation.deleted_at.is_(None)
                    ).first()

                    if not conversation:
                        conversation = Conversation(
                            org_id=person.org_id,
                            person_id=person.person_id,
                            channel_type="slack",
                            external_thread_id=channel,
                            status="active"
                        )
                        db.add(conversation)
                        db.commit()
                        db.refresh(conversation)

                    # Save inbound message
                    inbound_msg = Message(
                        org_id=person.org_id,
                        conversation_id=conversation.conversation_id,
                        direction="inbound",
                        sender_person_id=person.person_id,
                        content_text=text,
                        external_message_id=event.get("ts")
                    )
                    db.add(inbound_msg)
                    db.commit()

                    # Build context and process with orchestrator
                    context_builder = ContextBuilder(db)
                    context = context_builder.build_context(person.person_id, conversation.conversation_id)

                    orchestrator = OrchestratorAgent(db)
                    ai_response = orchestrator.process_message(
                        user_message=text,
                        person=person,
                        conversation=conversation,
                        context=context
                    )

                    # Save outbound message
                    outbound_msg = Message(
                        org_id=person.org_id,
                        conversation_id=conversation.conversation_id,
                        direction="outbound",
                        agent_name="orchestrator",
                        content_text=ai_response
                    )
                    db.add(outbound_msg)
                    db.commit()

                    # Send response
                    say(ai_response)

            except Exception as e:
                logger.error("Error handling Slack message", error=str(e), exc_info=True)
                say("I apologize, but I encountered an error processing your message. Please try again.")

    def start(self):
        """Start the Slack Socket Mode handler"""
        if not self.app:
            logger.warning("Slack app not initialized, skipping start")
            return

        handler = SocketModeHandler(self.app, settings.slack_app_token)
        logger.info("Starting Slack Socket Mode handler")
        handler.start()


# Create singleton instance
slack_integration = SlackIntegration()


def start_slack_integration():
    """Entry point to start Slack integration"""
    slack_integration.start()


if __name__ == "__main__":
    start_slack_integration()
