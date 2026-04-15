# models/meter.py

from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, uuid_pk


class Meter(Base, TimestampMixin):
    __tablename__ = "meters"

    id:                 Mapped[str]                = uuid_pk()
    site_id:            Mapped[str]                = mapped_column(String(36), ForeignKey("sites.id"), nullable=False, index=True)
    meter_number:       Mapped[str]                = mapped_column(String(100), unique=True,           nullable=False)
    supplier_device_id: Mapped[Optional[str]]      = mapped_column(String(100),                        nullable=True)
    meter_size_dn:      Mapped[Optional[str]]      = mapped_column(String(20),                         nullable=True)
    floor:              Mapped[Optional[str]]      = mapped_column(String(50),                         nullable=True)
    communication_mode: Mapped[Optional[str]]      = mapped_column(String(50),                         nullable=True)
    collector_id:       Mapped[Optional[str]]      = mapped_column(String(100),                        nullable=True)
    install_date:       Mapped[Optional[date]]     = mapped_column(Date,                               nullable=True)
    status:             Mapped[str]                = mapped_column(String(50), default="active",       nullable=False)
    last_read_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),            nullable=True)
    last_read_kwh:      Mapped[Optional[Decimal]]  = mapped_column(Numeric(15, 3),                     nullable=True)
    valve_status:       Mapped[Optional[str]]      = mapped_column(String(20),                         nullable=True)

    # Relationships
    site: Mapped[Site] = relationship("Site", back_populates="meters")
    readings: Mapped[list[MeterReading]] = relationship(
        "MeterReading", back_populates="meter", cascade="all, delete-orphan"
    )
    assignments: Mapped[list[MeterAssignment]] = relationship(
        "MeterAssignment", back_populates="meter", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Meter id={self.id!r} meter_number={self.meter_number!r} status={self.status!r}>"
