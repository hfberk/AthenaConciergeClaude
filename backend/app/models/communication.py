"""Communication infrastructure models"""

from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, UUID, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class CommIdentity(Base):
    """Maps persons to communication channels"""

    __tablename__ = "comm_identities"

    comm_identity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False, index=True)  # email, slack, sms, phone, web
    identity_value = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    person = relationship("Person", back_populates="comm_identities")
    reminder_rules = relationship("ReminderRule", back_populates="comm_identity")


class CommConsent(Base):
    """GDPR-compliant communication consent tracking"""

    __tablename__ = "comm_consent"

    consent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False)
    consent_given = Column(Boolean, nullable=False, default=True)
    consent_date = Column(DateTime, nullable=False, default=TimestampMixin.created_at.default.arg)
    expires_at = Column(DateTime)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)


class Conversation(Base):
    """Conversation threads"""

    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False)
    external_thread_id = Column(String(500), index=True)  # Slack thread_ts, email Message-ID
    subject = Column(String(500))
    status = Column(String(50), default="active")  # active, closed, archived
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    person = relationship("Person", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    working_memories = relationship("WorkingMemory", back_populates="conversation")


class Message(Base):
    """Individual messages within conversations"""

    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # inbound, outbound
    sender_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"))
    agent_name = Column(String(100))  # Which AI agent generated this
    content_text = Column(Text, nullable=False)
    content_html = Column(Text)
    external_message_id = Column(String(500))
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(DateTime, nullable=False, default=TimestampMixin.created_at.default.arg, index=True)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("Person", foreign_keys=[sender_person_id])
