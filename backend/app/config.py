"""Application configuration"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "AI Concierge Platform"
    app_version: str = "2.0.0"
    environment: str = "development"
    app_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    secret_key: str
    debug: bool = False

    # Database
    database_url: str
    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: str

    # Anthropic AI
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # OpenAI (for embeddings)
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Slack
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_signing_secret: str = ""

    # AWS SES
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    ses_email: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Vector Search
    vector_dimensions: int = 1536

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
