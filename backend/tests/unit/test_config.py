"""Unit tests for configuration"""

import pytest


@pytest.mark.unit
def test_get_settings_returns_settings_instance():
    """Test that get_settings returns a Settings instance"""
    from app.config import get_settings

    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "app_name")
    assert hasattr(settings, "app_version")


@pytest.mark.unit
def test_settings_has_required_attributes():
    """Test that settings has all required attributes"""
    from app.config import get_settings

    settings = get_settings()

    # Check for essential settings
    assert hasattr(settings, "supabase_url")
    assert hasattr(settings, "supabase_service_key")
    assert hasattr(settings, "anthropic_api_key")


@pytest.mark.unit
def test_settings_singleton_pattern():
    """Test that get_settings returns the same instance"""
    from app.config import get_settings

    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
