"""Test Slack connection and event handling"""

import structlog
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from app.config import get_settings

structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
)
logger = structlog.get_logger()

settings = get_settings()

print("=" * 60)
print("SLACK CONNECTION DIAGNOSTIC")
print("=" * 60)

# Check tokens
print(f"\n✓ Bot Token: {settings.slack_bot_token[:20]}..." if settings.slack_bot_token else "✗ Bot Token: NOT SET")
print(f"✓ App Token: {settings.slack_app_token[:20]}..." if settings.slack_app_token else "✗ App Token: NOT SET")

if not settings.slack_bot_token or not settings.slack_app_token:
    print("\n❌ ERROR: Tokens not configured!")
    exit(1)

# Test bot token validity
print("\n" + "=" * 60)
print("Testing bot token validity...")
print("=" * 60)

try:
    app = App(token=settings.slack_bot_token)
    auth_test = app.client.auth_test()
    print(f"\n✓ Bot is authenticated!")
    print(f"  Bot User ID: {auth_test['user_id']}")
    print(f"  Bot Name: {auth_test['user']}")
    print(f"  Team: {auth_test['team']}")
except Exception as e:
    print(f"\n❌ Bot token invalid: {e}")
    exit(1)

# Register test message handler
print("\n" + "=" * 60)
print("Registering message event handler...")
print("=" * 60)

@app.event("message")
def test_message_handler(event, say):
    print(f"\n🎉 MESSAGE RECEIVED!")
    print(f"  Event: {event}")
    print(f"  User: {event.get('user')}")
    print(f"  Text: {event.get('text')}")
    print(f"  Channel: {event.get('channel')}")
    print(f"  Bot ID: {event.get('bot_id')}")

    # Echo back
    if not event.get("bot_id"):
        say(f"✅ I received your message: {event.get('text')}")

print("✓ Message handler registered")

# Start Socket Mode
print("\n" + "=" * 60)
print("Starting Socket Mode connection...")
print("=" * 60)
print("\n🚀 Bot is now listening for messages!")
print("   Send a DM to your bot to test.")
print("   Press Ctrl+C to stop.\n")

try:
    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()
except KeyboardInterrupt:
    print("\n\n👋 Shutting down...")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
