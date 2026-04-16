# tests/test_ingestion_service.py
#
# Unit tests for ingestion/service.py.
# All API calls and DB sessions are mocked — no live connections required.
#
# Note: run from the repository root:
#   python -m unittest tests/test_ingestion_service.py

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from ingestion.service import (
    MeterNotFoundError,
    MeterNumberMismatchError,
    ingest_latest_reading,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────

MOCK_METER_ID     = "abc-123-uuid"
MOCK_METER_NUMBER = "0025091007"
MOCK_READ_AT      = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

MOCK_PAYLOAD = {
    "meter_number":    MOCK_METER_NUMBER,
    "read_at":         MOCK_READ_AT,
    "read_kwh":        Decimal("97170"),
    "signal_strength": -85,
    "valve_state":     "1",
}


def _make_mock_meter(meter_id=MOCK_METER_ID, meter_number=MOCK_METER_NUMBER):
    meter = MagicMock()
    meter.id           = meter_id
    meter.meter_number = meter_number
    return meter


def _make_mock_db(meter=None, duplicate=False):
    db = MagicMock()
    db.get.return_value = meter
    db.query.return_value.filter.return_value.first.return_value = (
        MagicMock() if duplicate else None
    )
    return db


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestIngestLatestReading(unittest.TestCase):

    @patch("ingestion.service.get_latest_reading", return_value=MOCK_PAYLOAD)
    def test_inserts_new_reading(self, _mock_api):
        """Happy path: new reading is inserted and meter fields are updated."""
        meter = _make_mock_meter()
        db    = _make_mock_db(meter=meter, duplicate=False)

        result = ingest_latest_reading(db, MOCK_METER_ID)

        self.assertEqual(result["status"],    "inserted")
        self.assertEqual(result["meter_id"],  MOCK_METER_ID)
        self.assertEqual(result["read_at"],   MOCK_READ_AT)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        self.assertEqual(meter.last_read_at,  MOCK_READ_AT)
        self.assertEqual(meter.last_read_kwh, Decimal("97170"))
        self.assertEqual(meter.valve_status,  "1")

    @patch("ingestion.service.get_latest_reading", return_value=MOCK_PAYLOAD)
    def test_returns_duplicate_status(self, _mock_api):
        """Duplicate reading returns status dict without inserting or committing."""
        meter = _make_mock_meter()
        db    = _make_mock_db(meter=meter, duplicate=True)

        result = ingest_latest_reading(db, MOCK_METER_ID)

        self.assertEqual(result["status"],   "duplicate")
        self.assertEqual(result["meter_id"], MOCK_METER_ID)
        self.assertEqual(result["read_at"],  MOCK_READ_AT)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_raises_meter_not_found(self):
        """Raises MeterNotFoundError before calling the API when meter_id is unknown."""
        db = _make_mock_db(meter=None)

        with self.assertRaises(MeterNotFoundError):
            ingest_latest_reading(db, "nonexistent-id")

    @patch("ingestion.service.get_latest_reading", return_value={
        **MOCK_PAYLOAD,
        "meter_number": "WRONG_METER",
    })
    def test_raises_on_meter_number_mismatch(self, _mock_api):
        """Raises MeterNumberMismatchError when API meter_number ≠ DB meter_number."""
        meter = _make_mock_meter(meter_number=MOCK_METER_NUMBER)
        db    = _make_mock_db(meter=meter)

        with self.assertRaises(MeterNumberMismatchError):
            ingest_latest_reading(db, MOCK_METER_ID)


if __name__ == "__main__":
    unittest.main()
