"""API routes"""

from fastapi import APIRouter

from app.api import persons, projects, conversations, agents, webhooks

router = APIRouter()

# Include sub-routers
router.include_router(persons.router, prefix="/persons", tags=["persons"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
