"""FastAPI main application"""

import os
import threading
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import health_check
from app.api import router as api_router

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("Starting AI Concierge Platform", version=settings.app_version)
    if not health_check():
        logger.error("Database health check failed at startup!")

    # Start Slack integration in background thread (user mode only)
    if settings.slack_user_token and settings.slack_app_token and settings.slack_bot_token:
        logger.info("Starting Slack Socket Mode integration (User mode - as Athena Concierge)")
        from app.integrations.slack_user import start_slack_user_integration
        slack_thread = threading.Thread(target=start_slack_user_integration, daemon=True)
        slack_thread.start()
        logger.info("Slack user integration started in background thread")
    else:
        logger.warning(
            "Slack user mode credentials not configured (requires slack_user_token, "
            "slack_app_token, and slack_bot_token). Slack integration disabled."
        )

    # Start background workers
    logger.info("Starting background workers")

    # Reminder worker (runs every 5 minutes)
    from app.workers.reminder_worker import run_reminder_worker
    reminder_thread = threading.Thread(target=run_reminder_worker, daemon=True)
    reminder_thread.start()
    logger.info("Reminder worker started in background thread")

    # Proactive worker (runs daily)
    from app.workers.proactive_worker import run_proactive_worker
    proactive_thread = threading.Thread(target=run_proactive_worker, daemon=True)
    proactive_thread.start()
    logger.info("Proactive worker started in background thread")

    yield

    # Shutdown
    logger.info("Shutting down AI Concierge Platform")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready AI concierge platform for high-net-worth clients",
    lifespan=lifespan
)

# CORS middleware
replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
allowed_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://localhost:5000",
    "https://localhost:5000",
    "http://127.0.0.1:5000",
    "https://127.0.0.1:5000"
]
if replit_domain:
    allowed_origins.extend([
        f"https://{replit_domain}",
        f"http://{replit_domain}"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception",
                 path=request.url.path,
                 method=request.method,
                 error=str(exc),
                 exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    db_healthy = health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": settings.app_version,
        "database": "connected" if db_healthy else "disconnected"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
