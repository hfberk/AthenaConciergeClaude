"""Project and task models"""

from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, UUID, Date, Text, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class Project(Base):
    """High-level concierge requests"""

    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    assigned_to_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), index=True)
    source_date_item_id = Column(UUID(as_uuid=True), ForeignKey("date_items.date_item_id"), index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=3)  # 1=highest, 4=lowest
    status = Column(String(50), default="new", index=True)  # new, in_progress, blocked, completed, cancelled
    due_date = Column(Date)
    completed_at = Column(DateTime)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    person = relationship("Person", back_populates="projects")
    assigned_to = relationship("Account", foreign_keys=[assigned_to_account_id])
    source_date_item = relationship("DateItem", back_populates="projects")
    details = relationship("ProjectDetail", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    recommendations = relationship("Recommendation", back_populates="project")


class ProjectDetail(Base):
    """Large/flexible project data"""

    __tablename__ = "project_details"

    project_detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    detail_type = Column(String(100), nullable=False)
    content_jsonb = Column(JSON, nullable=False)
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)

    # Relationships
    project = relationship("Project", back_populates="details")


class Task(Base):
    """Subtasks within projects"""

    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), index=True)
    assigned_to_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="todo")  # todo, doing, blocked, done, cancelled
    due_date = Column(Date)
    completed_at = Column(DateTime)
    sort_order = Column(Integer, default=0, index=True)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_to = relationship("Account", foreign_keys=[assigned_to_account_id])
    parent = relationship("Task", remote_side=[task_id], backref="subtasks")
