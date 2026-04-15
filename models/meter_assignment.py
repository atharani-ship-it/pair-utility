# models/meter_assignment.py

from __future__ import annotations

from decimal import Decimal
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, uuid_pk


class MeterAssignment(Base, TimestampMixin):
    __tablename__ = "meter_assignments"

    id:                  Mapped[str]               = uuid_pk()
    meter_id:            Mapped[str]               = mapped_column(String(36), ForeignKey("meters.id"),  nullable=False, index=True)
    tenant_id:           Mapped[str]               = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    assigned_from:       Mapped[date]              = mapped_column(Date,                                  nullable=False)
    assigned_to:         Mapped[Optional[date]]    = mapped_column(Date,                                  nullable=True)  # null = currently active
    opening_read_kwh:    Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3),                        nullable=True)
    closing_read_kwh:    Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3),                        nullable=True)
    opening_cert_signed: Mapped[bool]              = mapped_column(Boolean, default=False,                nullable=False)
    closing_cert_signed: Mapped[bool]              = mapped_column(Boolean, default=False,                nullable=False)

    # Relationships
    meter:  Mapped[Meter]  = relationship("Meter",  back_populates="assignments")
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="meter_assignments")
