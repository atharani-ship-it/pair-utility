# models/site.py

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, uuid_pk


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id:        Mapped[str]           = uuid_pk()
    site_code: Mapped[str]           = mapped_column(String(50),  unique=True, nullable=False)
    name:      Mapped[str]           = mapped_column(String(200), nullable=False)
    address:   Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city:      Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country:   Mapped[str]           = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool]          = mapped_column(Boolean,     nullable=False, default=True)
    notes:     Mapped[Optional[str]] = mapped_column(Text,        nullable=True)

    # Relationships
    tenants: Mapped[list[Tenant]] = relationship(
        "Tenant", back_populates="site", cascade="all, delete-orphan"
    )
    meters: Mapped[list[Meter]] = relationship(
        "Meter", back_populates="site", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Site id={self.id!r} site_code={self.site_code!r} name={self.name!r}>"
