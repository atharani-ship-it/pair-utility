# tests/test_calculator.py
#
# Validation tests for billing/calculator.py.
# Uses Python's built-in unittest — no additional dependencies required.
#
# Note: run from the repository root:
#   python -m unittest tests/test_calculator.py

import unittest
from decimal import Decimal

# Note: this import assumes the project is executed from the repository root.
from billing.calculator import calculate_bill


class TestCalculateBill(unittest.TestCase):

    def test_known_values_from_brief(self):
        """
        Validates the billing formula against the reference case in the brief.
        opening = 28410, closing = 62020 → grand_total must equal 9622.21
        """
        result = calculate_bill(opening_read=28410, closing_read=62020)
        self.assertEqual(result["grand_total"], Decimal("9622.21"))

    def test_closing_less_than_opening_raises(self):
        """closing_read < opening_read must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_bill(opening_read=62020, closing_read=28410)

    def test_equal_reads_produce_zero_usage(self):
        """Equal reads = zero consumption. Only service fee + VAT are charged."""
        result = calculate_bill(opening_read=10000, closing_read=10000)
        self.assertEqual(result["usage_kwh"], Decimal("0"))
        # subtotal = 0 + 85.00 = 85.00; vat = 4.25; grand_total = 89.25
        self.assertEqual(result["grand_total"], Decimal("89.25"))


if __name__ == "__main__":
    unittest.main()
