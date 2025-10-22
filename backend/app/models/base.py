"""Base model classes and mixins"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, UUID
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin:
    """Adds created_at and updated_at timestamps"""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """Adds soft delete functionality"""

    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class OrgScopedMixin:
    """Adds org_id for multi-tenancy"""

    @declared_attr
    def org_id(cls):
        return Column(UUID(as_uuid=True), nullable=False, index=True)


class BaseModel(TimestampMixin, SoftDeleteMixin, OrgScopedMixin):
    """Base model with all common mixins"""
    pass
