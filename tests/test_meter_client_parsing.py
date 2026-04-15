# tests/test_meter_client_parsing.py
#
# Tests for meter/client.py response parsing and input validation.
# All HTTP calls are mocked — no live API connection required.
#
# Note: run from the repository root:
#   python -m unittest tests/test_meter_client_parsing.py

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from meter.client import (
    MeterAPIError,
    _parse_reading_item,
    _validate_meter_response,
    set_valve_state,
)

# ── Known response fixtures ───────────────────────────────────────────────────

LIVE_RESPONSE = [
    {
        "code": 0,
        "data": [
            {
                "currentReading": "97170",
                "sysReadTime": "1709251200",  # 2024-03-01 00:00:00 UTC
                "signalStrength": -85,
                "valveState": 1,
            }
        ],
    }
]

HISTORICAL_RESPONSE = [
    {
        "code": 0,
        "data": [
            {
                "currentReading": "28410",
                "sysReadTime": "1735689600",
                "signalStrength": -80,
                "valveState": 1,
            },
            {
                "currentReading": "62020",
                "sysReadTime": "1738368000",
                "signalStrength": -82,
                "valveState": 1,
            },
        ],
    }
]

# ── Parsing tests ─────────────────────────────────────────────────────────────

class TestParseReadingItem(unittest.TestCase):

    def test_live_response_shape(self):
        """Parses the known live API reading response correctly."""
        result = _parse_reading_item(LIVE_RESPONSE[0]["data"][0])

        self.assertEqual(result["read_kwh"], Decimal("97170"))
        self.assertIsInstance(result["read_at"], datetime)
        self.assertEqual(result["read_at"].tzinfo, timezone.utc)
        self.assertEqual(result["signal_strength"], -85)
        self.assertEqual(result["valve_state"], "1")

    def test_historical_response_shape(self):
        """Parses all items from the known historical API response correctly."""
        results = [_parse_reading_item(item) for item in HISTORICAL_RESPONSE[0]["data"]]

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["read_kwh"], Decimal("28410"))
        self.assertEqual(results[1]["read_kwh"], Decimal("62020"))
        for result in results:
            self.assertIsInstance(result["read_at"], datetime)
            self.assertEqual(result["read_at"].tzinfo, timezone.utc)
            self.assertEqual(result["valve_state"], "1")

    def test_missing_timestamp_returns_none(self):
        """A missing sysReadTime produces read_at=None without raising."""
        result = _parse_reading_item({"currentReading": "1000"})
        self.assertIsNone(result["read_at"])
        self.assertEqual(result["read_kwh"], Decimal("1000"))

    def test_missing_optional_fields_return_none(self):
        """Missing signalStrength and valveState produce None, not an error."""
        result = _parse_reading_item({"currentReading": "500", "sysReadTime": "1709251200"})
        self.assertIsNone(result["signal_strength"])
        self.assertIsNone(result["valve_state"])


# ── Response validation tests ─────────────────────────────────────────────────

class TestValidateMeterResponse(unittest.TestCase):

    def test_rejects_non_dict_response(self):
        """A non-list at the top level is rejected."""
        with self.assertRaises(MeterAPIError):
            _validate_meter_response({}, "test")

    def test_rejects_empty_list(self):
        """An empty list is rejected."""
        with self.assertRaises(MeterAPIError):
            _validate_meter_response([], "test")

    def test_rejects_nonzero_code(self):
        """A non-zero code in the payload is treated as an API error."""
        with self.assertRaises(MeterAPIError):
            _validate_meter_response([{"code": 1, "data": [{"currentReading": "1"}]}], "test")

    def test_rejects_empty_data(self):
        """An empty data array is rejected."""
        with self.assertRaises(MeterAPIError):
            _validate_meter_response([{"code": 0, "data": []}], "test")

    def test_rejects_missing_data_key(self):
        """A missing data key is rejected."""
        with self.assertRaises(MeterAPIError):
            _validate_meter_response([{"code": 0}], "test")

    def test_valid_response_returns_items(self):
        """A well-formed response returns the data list."""
        items = _validate_meter_response(LIVE_RESPONSE, "test")
        self.assertEqual(len(items), 1)


# ── Valve state tests ─────────────────────────────────────────────────────────

class TestSetValveState(unittest.TestCase):

    def test_rejects_state_2(self):
        """State 2 is not accepted."""
        with self.assertRaises(ValueError):
            set_valve_state(2)

    def test_rejects_negative_state(self):
        """Negative values are not accepted."""
        with self.assertRaises(ValueError):
            set_valve_state(-1)

    def test_rejects_string_state(self):
        """String values are not accepted."""
        with self.assertRaises(ValueError):
            set_valve_state("open")

    @patch("meter.client.requests.post")
    @patch("meter.client.get_access_token", return_value="mock_token")
    def test_returns_true_on_cmd_success(self, _mock_token, mock_post):
        """Returns True when code==0 and cmdState==0."""
        mock_post.return_value = MagicMock(**{"json.return_value": {"code": 0, "cmdState": 0}})
        self.assertTrue(set_valve_state(1))

    @patch("meter.client.requests.post")
    @patch("meter.client.get_access_token", return_value="mock_token")
    def test_returns_false_on_cmd_failure(self, _mock_token, mock_post):
        """Returns False when cmdState is not 0."""
        mock_post.return_value = MagicMock(**{"json.return_value": {"code": 0, "cmdState": 1}})
        self.assertFalse(set_valve_state(0))


if __name__ == "__main__":
    unittest.main()
