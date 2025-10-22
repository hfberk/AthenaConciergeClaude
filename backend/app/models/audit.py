"""System audit models"""

from uuid import uuid4
from sqlalchemy import Column, String, UUID, JSON, DateTime
from app.database import Base
from app.models.base import TimestampMixin


class EventLog(Base):
    """Unified audit log"""

    __tablename__ = "event_log"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False, index=True)  # person, agent, system
    actor_id = Column(UUID(as_uuid=True), index=True)  # person_id, agent_id, or NULL
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    details_jsonb = Column(JSON, default={})
    created_at = Column(DateTime, nullable=False, default=TimestampMixin.created_at.default.arg, index=True)
