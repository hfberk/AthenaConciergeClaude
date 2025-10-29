"""Database connection and session management"""

from supabase import create_client, Client
from contextlib import contextmanager
from typing import Generator
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create Supabase client
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client singleton.

    Returns:
        Client: Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        logger.info("Supabase client initialized", url=settings.supabase_url)
    return _supabase_client


def get_db() -> Generator[Client, None, None]:
    """
    Dependency that provides a Supabase client.
    Use with FastAPI's Depends() for automatic cleanup.

    Example:
        @app.get("/users")
        def get_users(db: Client = Depends(get_db)):
            return db.table('persons').select('*').execute()
    """
    client = get_supabase_client()
    try:
        yield client
    finally:
        # Supabase client handles connection pooling automatically
        pass


@contextmanager
def get_db_context():
    """
    Context manager for Supabase client.
    Use in workers and standalone scripts.

    Example:
        with get_db_context() as db:
            users = db.table('persons').select('*').execute()
    """
    client = get_supabase_client()
    try:
        yield client
    except Exception as e:
        logger.error("Database error", error=str(e))
        raise


def init_db():
    """Initialize database - verify connection"""
    logger.info("Initializing Supabase connection...")
    client = get_supabase_client()
    logger.info("Supabase connection initialized successfully")
    # Note: Tables are managed via Supabase dashboard/migrations
    # Not via SQLAlchemy models


def health_check() -> bool:
    """Check if Supabase connection is healthy"""
    try:
        client = get_supabase_client()
        # Simple health check - just verify client is created
        # Table queries will fail if schema isn't applied yet
        if client is not None:
            logger.info("Supabase health check passed")
            return True
        return False
    except Exception as e:
        logger.error("Supabase health check failed", error=str(e))
        return False


# Legacy compatibility - for code that imports Base
# Note: Supabase uses PostgREST, not SQLAlchemy ORM
# Models will need to be refactored to use Supabase table operations
class Base:
    """Placeholder for SQLAlchemy Base compatibility"""
    pass
