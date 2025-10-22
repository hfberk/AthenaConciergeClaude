"""Recommendation and vetted resource models"""

from uuid import uuid4
from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, UUID, Text, JSON, Integer, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, OrgScopedMixin


class Vendor(Base):
    """Vetted service providers"""

    __tablename__ = "vendors"

    vendor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    vendor_type = Column(String(100), nullable=False, index=True)  # florist, caterer, photographer
    description = Column(Text)
    rating = Column(Numeric(2, 1))  # 1.0-5.0
    price_band = Column(String(10))  # $, $$, $$$, $$$$
    contact_info_jsonb = Column(JSON)
    tags_jsonb = Column(JSON, default=[])
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)


class Venue(Base):
    """Event spaces"""

    __tablename__ = "venues"

    venue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    venue_type = Column(String(100))  # restaurant, event_space, hotel
    description = Column(Text)
    capacity_min = Column(Integer, index=True)
    capacity_max = Column(Integer, index=True)
    price_band = Column(String(10))
    location_jsonb = Column(JSON)  # {neighborhood, city, state}
    private_rooms_jsonb = Column(JSON, default=[])
    contact_info_jsonb = Column(JSON)
    tags_jsonb = Column(JSON, default=[])
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)


class Restaurant(Base):
    """Dining recommendations"""

    __tablename__ = "restaurants"

    restaurant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    cuisine = Column(String(100), index=True)
    neighborhood = Column(String(100), index=True)
    description = Column(Text)
    rating = Column(Numeric(2, 1))
    price_band = Column(String(10))
    private_dining_jsonb = Column(JSON)  # {available, capacity, pricing}
    contact_info_jsonb = Column(JSON)
    tags_jsonb = Column(JSON, default=[])
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)


class Product(Base):
    """Gift ideas and shopping recommendations"""

    __tablename__ = "products"

    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255))
    category = Column(String(100), index=True)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    price_band = Column(String(10))
    url = Column(Text)
    image_url = Column(Text)
    tags_jsonb = Column(JSON, default=[])
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)


class Recommendation(Base):
    """AI-generated recommendations"""

    __tablename__ = "recommendations"

    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False, index=True)  # vendor, venue, restaurant, product
    item_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    rationale_text = Column(Text)  # Why this was recommended
    score = Column(Numeric(3, 2))  # Relevance 0-1
    shown_at = Column(DateTime)
    metadata_jsonb = Column(JSON, default={})
    created_at = Column(TimestampMixin.created_at.type, nullable=False, default=TimestampMixin.created_at.default.arg)
    updated_at = Column(TimestampMixin.updated_at.type, nullable=False, default=TimestampMixin.updated_at.default.arg)
    deleted_at = Column(SoftDeleteMixin.deleted_at.type)

    # Relationships
    project = relationship("Project", back_populates="recommendations")
    feedback = relationship("InteractionFeedback", back_populates="recommendation")


class InteractionFeedback(Base):
    """Client feedback on recommendations"""

    __tablename__ = "interaction_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.recommendation_id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.person_id"), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # liked, disliked, used, ignored
    feedback_text = Column(Text)
    created_at = Column(DateTime, nullable=False, default=TimestampMixin.created_at.default.arg)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="feedback")
