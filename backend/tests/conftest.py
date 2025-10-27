"""Shared test fixtures for all tests"""

import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, MagicMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["TESTING"] = "1"


@pytest.fixture(scope="function")
def mock_supabase_client():
    """Mock Supabase client for individual tests"""
    client = MagicMock()
    # Mock common Supabase operations
    client.table.return_value.select.return_value.execute.return_value.data = []
    client.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1}]
    client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": 1}]
    client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    return client


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with minimal mocking.
    Individual tests should add specific mocks as needed.
    """
    # Mock database and settings at import time
    with patch("app.database.get_supabase_client") as mock_db, \
         patch("app.config.get_settings") as mock_settings:

        # Configure mock settings
        settings = MagicMock()
        settings.app_name = "AI Concierge Test"
        settings.app_version = "1.0.0-test"
        settings.debug = True
        settings.frontend_url = "http://localhost:3000"
        settings.supabase_url = "http://localhost:54321"
        settings.supabase_service_key = "test-key"
        settings.anthropic_api_key = "test-anthropic-key"
        settings.slack_bot_token = None  # Disable Slack in tests
        settings.slack_user_token = None
        settings.slack_app_token = None
        mock_settings.return_value = settings

        # Configure mock database
        mock_db.return_value = MagicMock()

        # Import app after mocks are set up
        from app.main import app

        # Use TestClient with raise_server_exceptions=False for cleaner test output
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async FastAPI test client with minimal mocking.
    Use this for testing async endpoints.
    """
    with patch("app.database.get_supabase_client") as mock_db, \
         patch("app.config.get_settings") as mock_settings:

        # Configure mock settings
        settings = MagicMock()
        settings.app_name = "AI Concierge Test"
        settings.app_version = "1.0.0-test"
        settings.debug = True
        settings.frontend_url = "http://localhost:3000"
        settings.supabase_url = "http://localhost:54321"
        settings.supabase_service_key = "test-key"
        settings.anthropic_api_key = "test-anthropic-key"
        settings.slack_bot_token = None
        settings.slack_user_token = None
        settings.slack_app_token = None
        mock_settings.return_value = settings

        # Configure mock database
        mock_db.return_value = MagicMock()

        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def mock_person_data():
    """Sample person data for testing"""
    return {
        "person_id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "John Doe",
        "preferred_name": "John",
        "person_type": "primary",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "timezone": "America/New_York"
    }


@pytest.fixture
def mock_household_data():
    """Sample household data for testing"""
    return {
        "household_id": "223e4567-e89b-12d3-a456-426614174000",
        "household_name": "Doe Family",
        "household_type": "family",
        "tier": "platinum"
    }


@pytest.fixture
def faker_seed():
    """Seed faker for consistent test data generation"""
    from faker import Faker
    fake = Faker()
    Faker.seed(12345)
    return fake


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Tests that take a long time")


def pytest_collection_modifyitems(config, items):
    """Add markers automatically based on test location"""
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
