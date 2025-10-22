"""Identity and multi-tenancy models"""

from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, UUID, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class Organization(Base):
    """Top-level tenant boundary"""

    __tablename__ = "organizations"

    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    settings_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    accounts = relationship("Account", back_populates="organization")
    persons = relationship("Person", back_populates="organization")


class Account(Base):
    """Staff accounts linked to Supabase auth"""

    __tablename__ = "accounts"

    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=False)
    auth_user_id = Column(UUID(as_uuid=True))
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # admin, concierge, analyst
    is_active = Column(Boolean, default=True)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    organization = relationship("Organization", back_populates="accounts")
    assigned_projects = relationship("Project", foreign_keys="Project.assigned_to_account_id")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to_account_id")


class Person(Base):
    """Universal person table (clients, family members, staff)"""

    __tablename__ = "persons"

    person_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=False, index=True)
    person_type = Column(String(50), nullable=False, index=True)  # client, staff, family_member
    full_name = Column(String(255), nullable=False)
    preferred_name = Column(String(100))
    birthday = Column(Date)
    timezone = Column(String(50), default="America/New_York")
    metadata_jsonb = Column(JSON, default={})  # Flexible preferences
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    organization = relationship("Organization", back_populates="persons")
    comm_identities = relationship("CommIdentity", back_populates="person")
    conversations = relationship("Conversation", back_populates="person")
    date_items = relationship("DateItem", back_populates="person")
    projects = relationship("Project", back_populates="person")
    household_members = relationship("HouseholdMember", back_populates="person")
