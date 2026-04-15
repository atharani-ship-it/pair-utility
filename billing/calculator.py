# billing/calculator.py
#
# Pure billing calculation module for the PAIR Utility Platform.
# No I/O, no API calls, no database logic — inputs in, dict out.
#
# All arithmetic uses Decimal with ROUND_HALF_UP to match the
# contractual billing formula defined in the project brief.

# Note: this import assumes the project is executed from the repository root.
from decimal import Decimal, ROUND_HALF_UP

from constants import (
    RTH_CONVERSION_FACTOR,
    RATE_PER_RTH,
    SERVICE_FEE,
    VAT_RATE,
)

_TWO_PLACES   = Decimal("0.01")
_FIVE_PLACES  = Decimal("0.00001")


def _quantize(value: Decimal) -> Decimal:
    """Round a Decimal to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_bill(opening_read, closing_read) -> dict:
    """
    Calculate the full billing breakdown for a given meter read pair.

    Applies the PAIR billing formula:
        usage_kwh          = closing_read - opening_read
        usage_rth          = round(usage_kwh / RTH_CONVERSION_FACTOR, 5)
        consumption_charge = round(usage_rth * RATE_PER_RTH, 2)
        subtotal           = round(consumption_charge + SERVICE_FEE, 2)
        vat                = round(subtotal * VAT_RATE, 2)
        grand_total        = round(subtotal + vat, 2)

    Args:
        opening_read: Opening meter reading in kWh (int, float, or Decimal).
        closing_read:  Closing meter reading in kWh (int, float, or Decimal).

    Returns:
        dict with keys:
            usage_kwh           (Decimal)
            usage_rth           (Decimal, 5 dp)
            consumption_charge  (Decimal, 2 dp)
            subtotal            (Decimal, 2 dp)
            vat                 (Decimal, 2 dp)
            grand_total         (Decimal, 2 dp)

    Raises:
        ValueError: If closing_read is less than opening_read.
    """
    opening = Decimal(str(opening_read))
    closing = Decimal(str(closing_read))

    if closing < opening:
        raise ValueError(
            f"closing_read ({closing}) must not be less than opening_read ({opening})."
        )

    usage_kwh          = closing - opening
    usage_rth          = (usage_kwh / RTH_CONVERSION_FACTOR).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
    consumption_charge = _quantize(usage_rth * RATE_PER_RTH)
    subtotal           = _quantize(consumption_charge + SERVICE_FEE)
    vat                = _quantize(subtotal * VAT_RATE)
    grand_total        = _quantize(subtotal + vat)

    return {
        "usage_kwh":          usage_kwh,
        "usage_rth":          usage_rth,
        "consumption_charge": consumption_charge,
        "subtotal":           subtotal,
        "vat":                vat,
        "grand_total":        grand_total,
    }
