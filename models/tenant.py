# models/tenant.py

from __future__ import annotations

from decimal import Decimal
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, uuid_pk


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id:               Mapped[str]               = uuid_pk()
    site_id:          Mapped[str]               = mapped_column(String(36), ForeignKey("sites.id"),   nullable=False, index=True)
    account_number:   Mapped[str]               = mapped_column(String(50),  unique=True,             nullable=False)
    legal_name:       Mapped[str]               = mapped_column(String(200),                          nullable=False)
    trade_license_no: Mapped[Optional[str]]     = mapped_column(String(100),                          nullable=True)
    trn:              Mapped[Optional[str]]     = mapped_column(String(50),                           nullable=True)
    unit_number:      Mapped[str]               = mapped_column(String(50),                           nullable=False)
    floor:            Mapped[Optional[str]]     = mapped_column(String(50),                           nullable=True)
    contact_name:     Mapped[Optional[str]]     = mapped_column(String(200),                          nullable=True)
    contact_phone:    Mapped[Optional[str]]     = mapped_column(String(50),                           nullable=True)
    contact_email:    Mapped[Optional[str]]     = mapped_column(String(200),                          nullable=True)
    billing_email:    Mapped[Optional[str]]     = mapped_column(String(200),                          nullable=True)
    whatsapp_number:  Mapped[Optional[str]]     = mapped_column(String(50),                           nullable=True)
    security_deposit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2),                       nullable=True)
    status:           Mapped[str]               = mapped_column(String(50),  default="active",        nullable=False)
    onboarding_date:  Mapped[Optional[date]]    = mapped_column(Date,                                 nullable=True)
    vacation_date:    Mapped[Optional[date]]    = mapped_column(Date,                                 nullable=True)

    # Relationships
    site: Mapped[Site] = relationship("Site", back_populates="tenants")
    meter_assignments: Mapped[list[MeterAssignment]] = relationship(
        "MeterAssignment", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id!r} account_number={self.account_number!r} legal_name={self.legal_name!r}>"
