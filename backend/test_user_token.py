"""Test Slack user token authentication"""

from slack_sdk import WebClient
from app.config import get_settings
import sys

settings = get_settings()

print("=" * 60)
print("SLACK USER TOKEN TEST")
print("=" * 60)

if not settings.slack_user_token:
    print("\n❌ SLACK_USER_TOKEN not configured in .env")
    sys.exit(1)

print(f"\n✓ User Token: {settings.slack_user_token[:20]}...")

try:
    client = WebClient(token=settings.slack_user_token)
    auth_response = client.auth_test()

    print("\n" + "=" * 60)
    print("✅ USER TOKEN AUTHENTICATION SUCCESSFUL")
    print("=" * 60)
    print(f"\nUser ID: {auth_response['user_id']}")
    print(f"User Name: {auth_response['user']}")
    print(f"Team: {auth_response['team']}")
    print(f"Team ID: {auth_response['team_id']}")

    # Test posting a message to see what scopes are available
    print("\n" + "=" * 60)
    print("Testing available scopes...")
    print("=" * 60)

    # List channels the user has access to
    try:
        channels = client.conversations_list(types="public_channel,private_channel", limit=5)
        print(f"\n✓ Can list conversations: YES")
        print(f"  Found {len(channels['channels'])} channels")
        for ch in channels['channels'][:3]:
            print(f"    - {ch['name']}")
    except Exception as e:
        print(f"\n✗ Cannot list conversations: {e}")

    # Check user info access
    try:
        user_info = client.users_info(user=auth_response['user_id'])
        print(f"\n✓ Can read user info: YES")
        print(f"  Real name: {user_info['user'].get('real_name')}")
        print(f"  Email: {user_info['user'].get('profile', {}).get('email', 'N/A')}")
    except Exception as e:
        print(f"\n✗ Cannot read user info: {e}")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("\n1. Make sure your Slack app has these Event Subscriptions:")
    print("   - message.channels")
    print("   - message.im")
    print("   - message.groups")
    print("   - message.mpim")
    print("\n2. Restart your backend to use the new user integration")
    print("\n3. Send a message in a channel where Athena Concierge is a member")
    print("   OR send a DM to the user")
    print("\n4. The response will appear to come from 'Athena Concierge' user,")
    print("   not from a bot!")

except Exception as e:
    print(f"\n❌ AUTHENTICATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
