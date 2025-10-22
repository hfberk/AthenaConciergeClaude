"""Date and reminder models"""

from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, UUID, Date, Text, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class DateCategory(Base):
    """Date categories (types of important dates)"""

    __tablename__ = "date_categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    icon = Column(String(50))
    color = Column(String(50))
    schema_jsonb = Column(JSON, default={})  # Category-specific fields
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    date_items = relationship("DateItem", back_populates="category")


class DateItem(Base):
    """Important dates"""

    __tablename__ = "date_items"

    date_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("date_categories.category_id"), nullable=False)
    title = Column(String(255), nullable=False)
    date_value = Column(Date, nullable=False)
    recurrence_rule = Column(Text)  # iCal RRULE format
    next_occurrence = Column(Date, index=True)  # Computed field
    notes = Column(Text)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    person = relationship("Person", back_populates="date_items")
    category = relationship("DateCategory", back_populates="date_items")
    reminder_rules = relationship("ReminderRule", back_populates="date_item")
    projects = relationship("Project", back_populates="source_date_item")


class ReminderRule(Base):
    """Reminder rules (when/how to notify)"""

    __tablename__ = "reminder_rules"

    reminder_rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    date_item_id = Column(UUID(as_uuid=True), ForeignKey("date_items.date_item_id"), nullable=False, index=True)
    comm_identity_id = Column(UUID(as_uuid=True), ForeignKey("comm_identities.comm_identity_id"), nullable=False)
    reminder_type = Column(String(50), nullable=False)  # lead_time, scheduled
    lead_time_days = Column(Integer)  # For lead_time type
    scheduled_datetime = Column(DateTime, index=True)  # For scheduled type
    sent_at = Column(DateTime)  # Tracks delivery
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    date_item = relationship("DateItem", back_populates="reminder_rules")
    comm_identity = relationship("CommIdentity", back_populates="reminder_rules")
