# models/base.py
#
# Shared SQLAlchemy base and reusable mixins.
# All table models in this project should inherit from Base.
# TimestampMixin and uuid_pk() are available for use in any model.

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all PAIR Utility table models."""
    pass


class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.

    created_at is set once on insert.
    updated_at is set on insert and refreshed automatically on every update.
    Both are stored in UTC.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def uuid_pk() -> Mapped[str]:
    """
    Column factory for a UUID primary key stored as a 36-character string.

    Usage in a model:
        id: Mapped[str] = uuid_pk()
    """
    return mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
