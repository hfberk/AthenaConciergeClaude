"""AI agent infrastructure models"""

from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, UUID, Text, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class AgentRoster(Base):
    """Configurable agent definitions"""

    __tablename__ = "agent_roster"

    agent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    agent_kind = Column(String(50), nullable=False)  # interaction, execution
    status = Column(String(50), default="active", index=True)  # active, paused, archived
    system_prompt = Column(Text, nullable=False)
    context_jsonb = Column(JSON, default={})  # Agent-specific configuration
    version = Column(Integer, default=1)
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    execution_logs = relationship("AgentExecutionLog", back_populates="agent")


class AgentExecutionLog(Base):
    """Complete audit trail of agent decisions"""

    __tablename__ = "agent_execution_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_roster.agent_id"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Groups related messages
    turn_index = Column(Integer, nullable=False)  # Order within conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"))
    payload_jsonb = Column(JSON, nullable=False)  # Full request/response
    execution_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=TimestampMixin.created_at.default.arg, index=True)

    # Relationships
    agent = relationship("AgentRoster", back_populates="execution_logs")


class Embedding(Base):
    """Vector embeddings for semantic search"""

    __tablename__ = "embeddings"

    embedding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # person, project, message, recommendation, preference
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Note: embedding_vector uses pgvector extension type - will be handled by raw SQL
    # embedding_vector = Column(Vector(1536))  # Requires pgvector extension
    content_text = Column(Text, nullable=False)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)


class WorkingMemory(Base):
    """Ephemeral agent state storage"""

    __tablename__ = "working_memory"

    memory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    memory_key = Column(String(255), nullable=False)
    memory_value_jsonb = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)

    # Relationships
    conversation = relationship("Conversation", back_populates="working_memories")
