"""Backend API Audit Script"""

import requests
import json
from app.database import get_db_context
from app.utils.supabase_helpers import SupabaseQuery

BASE_URL = "http://localhost:8000"

def audit_database():
    """Check what data exists in the database"""
    print("\n" + "=" * 60)
    print("DATABASE AUDIT")
    print("=" * 60)

    with get_db_context() as db:
        # Check organizations
        try:
            orgs = SupabaseQuery.select_active(db, 'organizations', limit=5)
            print(f"\n✓ Organizations: {len(orgs)} found")
            if orgs:
                for org in orgs:
                    print(f"  - {org.get('org_name')} ({org.get('org_id')})")
        except Exception as e:
            print(f"\n✗ Organizations: Error - {e}")

        # Check persons
        try:
            persons = SupabaseQuery.select_active(db, 'persons', limit=5)
            print(f"\n✓ Persons: {len(persons)} found")
            if persons:
                for person in persons:
                    print(f"  - {person.get('full_name')} ({person.get('person_type')}) - {person.get('person_id')}")
        except Exception as e:
            print(f"\n✗ Persons: Error - {e}")

        # Check projects
        try:
            projects = SupabaseQuery.select_active(db, 'projects', limit=5)
            print(f"\n✓ Projects: {len(projects)} found")
            if projects:
                for project in projects:
                    print(f"  - {project.get('title')} - {project.get('status')}")
        except Exception as e:
            print(f"\n✗ Projects: Error - {e}")

        # Check conversations
        try:
            conversations = SupabaseQuery.select_active(db, 'conversations', limit=5)
            print(f"\n✓ Conversations: {len(conversations)} found")
        except Exception as e:
            print(f"\n✗ Conversations: Error - {e}")

        # Check date_items
        try:
            date_items = SupabaseQuery.select_active(db, 'date_items', limit=5)
            print(f"\n✓ Date Items: {len(date_items)} found")
            if date_items:
                for item in date_items:
                    print(f"  - {item.get('title')} - {item.get('date_value')}")
        except Exception as e:
            print(f"\n✗ Date Items: Error - {e}")

        # Check reminder_rules
        try:
            reminders = SupabaseQuery.select_active(db, 'reminder_rules', limit=5)
            print(f"\n✓ Reminder Rules: {len(reminders)} found")
        except Exception as e:
            print(f"\n✗ Reminder Rules: Error - {e}")

        # Check date_categories
        try:
            categories = SupabaseQuery.select_active(db, 'date_categories', limit=10)
            print(f"\n✓ Date Categories: {len(categories)} found")
            if categories:
                for cat in categories:
                    print(f"  - {cat.get('category_name')} {cat.get('icon', '')}")
        except Exception as e:
            print(f"\n✗ Date Categories: Error - {e}")

def test_api_endpoints():
    """Test existing API endpoints"""
    print("\n" + "=" * 60)
    print("API ENDPOINTS TEST")
    print("=" * 60)

    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n✓ GET /health - {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"\n✗ GET /health - Error: {e}")

    # Test persons API (needs org_id - will use first org from DB)
    with get_db_context() as db:
        try:
            orgs = SupabaseQuery.select_active(db, 'organizations', limit=1)
            if orgs:
                org_id = orgs[0]['org_id']
                print(f"\n Testing with org_id: {org_id}")

                # Test list persons
                response = requests.get(
                    f"{BASE_URL}/api/v1/persons",
                    params={'org_id': org_id},
                    timeout=5
                )
                print(f"\n✓ GET /api/v1/persons - {response.status_code}")
                persons = response.json()
                print(f"  Found {len(persons)} persons")

                # Test list projects
                response = requests.get(
                    f"{BASE_URL}/api/v1/projects",
                    params={'org_id': org_id},
                    timeout=5
                )
                print(f"\n✓ GET /api/v1/projects - {response.status_code}")
                projects = response.json()
                print(f"  Found {len(projects)} projects")

                # Test list conversations
                response = requests.get(
                    f"{BASE_URL}/api/v1/conversations",
                    params={'org_id': org_id},
                    timeout=5
                )
                print(f"\n✓ GET /api/v1/conversations - {response.status_code}")
                conversations = response.json()
                print(f"  Found {len(conversations)} conversations")

        except Exception as e:
            print(f"\n✗ API Tests: Error - {e}")

def document_missing_apis():
    """Document what API endpoints are missing"""
    print("\n" + "=" * 60)
    print("MISSING API ENDPOINTS")
    print("=" * 60)

    missing = [
        "\nDate Items & Reminders:",
        "  - GET /api/v1/persons/{id}/date-items",
        "  - POST /api/v1/date-items",
        "  - PUT /api/v1/date-items/{id}",
        "  - DELETE /api/v1/date-items/{id}",
        "  - GET /api/v1/reminders",
        "  - POST /api/v1/reminders",
        "  - GET /api/v1/reminders/{id}/history",

        "\nDate Categories:",
        "  - GET /api/v1/date-categories",
        "  - POST /api/v1/date-categories",

        "\nDashboard:",
        "  - GET /api/v1/persons/{id}/dashboard",
        "  - GET /api/v1/persons/{id}/activity",

        "\nEnhanced Persons:",
        "  - PUT /api/v1/persons/{id}/profile (comprehensive update)",
        "  - GET /api/v1/persons/{id}/upcoming",

        "\nRecommendations:",
        "  - GET /api/v1/persons/{id}/recommendations"
    ]

    for item in missing:
        print(item)

if __name__ == "__main__":
    print("\n🔍 Starting Backend API Audit...\n")

    audit_database()
    test_api_endpoints()
    document_missing_apis()

    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60 + "\n")
