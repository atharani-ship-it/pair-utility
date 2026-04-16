# ingestion/service.py
#
# Pulls the latest reading from the meter API and persists it to the database.
# Designed to be called on demand — no background jobs, fully synchronous.

# Note: these imports assume the project is executed from the repository root.
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from meter.client import get_latest_reading
from models.meter import Meter
from models.meter_reading import MeterReading


class MeterNotFoundError(Exception):
    """Raised when no Meter row exists for the given meter_id."""
    pass


class MeterNumberMismatchError(Exception):
    """Raised when the API payload meter_number does not match the DB meter record."""
    pass


def _to_json_safe(payload: dict) -> dict:
    """
    Convert payload values to JSON-serializable types for raw_payload storage.
    Decimal → str, datetime → ISO 8601 string. All other values passed through.
    """
    result = {}
    for k, v in payload.items():
        if isinstance(v, Decimal):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


def ingest_latest_reading(db_session: Session, meter_id: str) -> dict:
    """
    Pull latest reading from API, persist it if not duplicate,
    update meter last-read fields, and return a result dict.

    Args:
        db_session: Active SQLAlchemy session.
        meter_id:   UUID primary key of the Meter row to ingest for.

    Returns:
        {"status": "inserted", "meter_id": ..., "read_at": ...}
        {"status": "duplicate", "meter_id": ..., "read_at": ...}

    Raises:
        MeterNotFoundError:       If no Meter row exists with the given meter_id.
        MeterNumberMismatchError: If the API payload meter_number does not match
                                  the meter_number stored on the Meter row.
    """
    # 1. Look up meter by primary key
    meter = db_session.get(Meter, meter_id)
    if meter is None:
        raise MeterNotFoundError(
            f"No Meter found with id={meter_id!r}."
        )

    # 2. Pull latest reading from API
    payload = get_latest_reading()

    # 3. Verify the API meter_number matches the DB record
    if payload["meter_number"] != meter.meter_number:
        raise MeterNumberMismatchError(
            f"API returned meter_number={payload['meter_number']!r} "
            f"but DB meter has meter_number={meter.meter_number!r}."
        )

    read_at: datetime = payload["read_at"]
    read_kwh: Decimal = payload["read_kwh"]

    # 4. Duplicate check: same (meter_id, read_at)
    existing = (
        db_session.query(MeterReading)
        .filter(
            MeterReading.meter_id == meter_id,
            MeterReading.read_at  == read_at,
        )
        .first()
    )
    if existing:
        return {"status": "duplicate", "meter_id": meter_id, "read_at": read_at}

    # 5. Insert new reading
    reading = MeterReading(
        meter_id=        meter_id,
        read_at=         read_at,
        read_kwh=        read_kwh,
        signal_strength= payload.get("signal_strength"),
        valve_state=     payload.get("valve_state"),
        source=          "api",
        is_estimated=    False,
        raw_payload=     _to_json_safe(payload),
    )
    db_session.add(reading)

    # 6. Update meter last-read fields
    meter.last_read_at  = read_at
    meter.last_read_kwh = read_kwh
    meter.valve_status  = payload.get("valve_state")

    # 7. Single commit
    db_session.commit()

    return {"status": "inserted", "meter_id": meter_id, "read_at": read_at}
