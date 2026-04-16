from __future__ import annotations

import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import requests
import streamlit as st

from constants import (
    API_BASE_URL,
    API_CLIENT_ID,
    API_METER_NO,
    API_TIMEOUT,
    API_USER_AGENT,
)
from meter.auth import get_access_token


class MeterAPIError(Exception):
    """Raised when the meter API returns an unexpected or error response."""
    pass


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_headers(token: str) -> dict:
    """Assemble the full required header set for every meter API request."""
    return {
        "content-Type": "application/json",
        "charset": "UTF-8",
        "access_token": token,
        "client_id": API_CLIENT_ID,
        "User-Agent": API_USER_AGENT,
    }


def _validate_meter_response(response: list, context: str) -> list:
    """
    Validate the meter API response envelope and return the data array.

    Expected shape: [{"code": 0, "data": [...]}]

    Raises:
        MeterAPIError: If the response is malformed or indicates an API error.
    """
    if not isinstance(response, list) or not response:
        raise MeterAPIError(
            f"{context}: expected non-empty list response, got {type(response).__name__}."
        )
    payload = response[0]
    if not isinstance(payload, dict):
        raise MeterAPIError(
            f"{context}: first element is not a dict, got {type(payload).__name__}."
        )
    if payload.get("code") != 0:
        raise MeterAPIError(
            f"{context}: API returned error code. Payload: {payload}"
        )
    items = payload.get("data")
    if not items or not isinstance(items, list):
        raise MeterAPIError(
            f"{context}: response data is missing or empty."
        )
    return items


def _parse_reading_item(item: dict) -> dict:
    """
    Parse a single reading object from the API data array.

    Returns a dict with:
        read_at         (datetime, UTC) or None if timestamp is missing/invalid
        read_kwh        (Decimal)
        signal_strength (int or None)
        valve_state     (str or None)
    """
    raw_ts = item.get("sysReadTime")
    read_at: Optional[datetime] = None
    if raw_ts:
        try:
            read_at = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc)
        except (ValueError, OSError):
            pass

    read_kwh = Decimal(item["currentReading"])

    raw_signal = item.get("signalStrength")
    raw_valve = item.get("valveState")

    return {
        "read_at": read_at,
        "read_kwh": read_kwh,
        "signal_strength": int(raw_signal) if raw_signal is not None else None,
        "valve_state": str(raw_valve) if raw_valve is not None else None,
    }


# ── Public interface ──────────────────────────────────────────────────────────

def get_latest_reading() -> dict:
    """
    Fetch the latest meter reading from the API.

    Returns:
        Returns parsed latest-reading payload.
    """
    if st.session_state.get("demo_mode", False):
        now = datetime.now(timezone.utc)
        read_kwh = Decimal(str(97170 + random.uniform(0, 80)))
        return {
            "meter_number": API_METER_NO,
            "read_at": now,
            "read_kwh": read_kwh,
            "signal_strength": 100,
            "valve_state": "1",
        }

    token = get_access_token()
    url = (
        f"{API_BASE_URL}/remoteData/getMeterData"
        f"?dataType=1&meterType=1&meterNo={API_METER_NO}"
    )
    try:
        response = requests.post(url, headers=_build_headers(token), timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MeterAPIError(f"get_latest_reading request failed: {exc}") from exc

    items = _validate_meter_response(data, "get_latest_reading")
    parsed = _parse_reading_item(items[0])
    parsed["meter_number"] = API_METER_NO
    return parsed


def get_historical_readings(start_time: datetime, end_time: datetime) -> list[dict]:
    """
    Fetch historical meter readings for a given date range.

    Args:
        start_time: Start of the billing period (beginTime set to 00:00:00).
        end_time:   End of the billing period   (endTime   set to 23:59:59).

    Returns:
        Returns parsed historical-reading payload.
    """
    token = get_access_token()
    begin = start_time.strftime("%Y-%m-%d 00:00:00")
    end = end_time.strftime("%Y-%m-%d 23:59:59")
    url = (
        f"{API_BASE_URL}/remoteData/getMeterData"
        f"?dataType=2&meterType=1&meterNo={API_METER_NO}"
        f"&beginTime={begin}&endTime={end}"
    )
    try:
        response = requests.post(url, headers=_build_headers(token), timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MeterAPIError(f"get_historical_readings request failed: {exc}") from exc

    items = _validate_meter_response(data, "get_historical_readings")
    return [_parse_reading_item(item) for item in items]


def set_valve_state(state: int) -> bool:
    """
    Open or close the chilled water valve for the configured meter.

    Args:
        state: 0 to close (suspend service), 1 to open (restore service).

    Returns:
        Returns True/False based on API command acceptance.

    Raises:
        ValueError:    If state is not 0 or 1.
        MeterAPIError: If the API request fails or returns an error.
    """
    if state not in (0, 1):
        raise ValueError(
            f"Invalid valve state: {state!r}. Must be 0 (close) or 1 (open)."
        )

    token = get_access_token()
    url = (
        f"{API_BASE_URL}/remoteData/setValveState"
        f"?meterNo={API_METER_NO}&valveState={state}"
    )
    try:
        response = requests.post(url, headers=_build_headers(token), timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MeterAPIError(f"set_valve_state request failed: {exc}") from exc

    if not isinstance(data, dict):
        raise MeterAPIError(
            f"set_valve_state: unexpected response shape: {data}"
        )
    if data.get("code") != 0:
        raise MeterAPIError(
            f"set_valve_state: API returned error. Response: {data}"
        )

    return data.get("cmdState") == 0