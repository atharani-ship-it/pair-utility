# models/meter_reading.py

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, uuid_pk


class MeterReading(Base, TimestampMixin):
    __tablename__ = "meter_readings"

    id:              Mapped[str]            = uuid_pk()
    meter_id:        Mapped[str]            = mapped_column(String(36), ForeignKey("meters.id"), nullable=False, index=True)
    read_at:         Mapped[datetime]       = mapped_column(DateTime(timezone=True),             nullable=False, index=True)
    read_kwh:        Mapped[Decimal]        = mapped_column(Numeric(15, 3),                      nullable=False)
    signal_strength: Mapped[Optional[int]]  = mapped_column(Integer,                              nullable=True)
    valve_state:     Mapped[Optional[str]]  = mapped_column(String(20),                          nullable=True)
    source:          Mapped[str]            = mapped_column(String(50),                          nullable=False)  # 'api', 'manual', 'estimated'
    is_estimated:    Mapped[bool]           = mapped_column(Boolean, default=False,              nullable=False)
    raw_payload:     Mapped[Optional[Any]]  = mapped_column(JSON,                                nullable=True)

    # Relationships
    meter: Mapped[Meter] = relationship("Meter", back_populates="readings")
