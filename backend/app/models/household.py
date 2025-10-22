"""Household and address models"""

from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, UUID, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class Household(Base):
    """Physical properties"""

    __tablename__ = "households"

    household_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    household_name = Column(String(255), nullable=False)
    household_type = Column(String(100))  # Primary Residence, Vacation Home, etc.
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    members = relationship("HouseholdMember", back_populates="household")
    addresses = relationship("Address", back_populates="household")


class HouseholdMember(Base):
    """Links persons to households"""

    __tablename__ = "household_members"

    household_member_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    household_id = Column(UUID(as_uuid=True), ForeignKey("households.household_id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    relationship_to_primary = Column(String(100))  # owner, spouse, child, staff
    is_primary = Column(Boolean, default=False)
    moved_in_date = Column(Date)
    moved_out_date = Column(Date)
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    household = relationship("Household", back_populates="members")
    person = relationship("Person", back_populates="household_members")


class Address(Base):
    """Structured addresses (can belong to households or persons)"""

    __tablename__ = "addresses"

    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    household_id = Column(UUID(as_uuid=True), ForeignKey("households.household_id"), index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), index=True)
    label = Column(String(100))  # Primary, Billing, Shipping
    address_jsonb = Column(JSON, nullable=False)  # {street, city, state, postal_code, country}
    is_primary = Column(Boolean, default=False)
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    household = relationship("Household", back_populates="addresses")
