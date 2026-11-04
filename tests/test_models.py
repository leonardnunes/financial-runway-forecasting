"""Unit tests for validated financial input models."""

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from financial_runway_forecasting.models import (
    MonthlyRecord,
    Scenario,
    parse_nonnegative_decimal,
    validate_period,
)


class MonthlyRecordTests(unittest.TestCase):

    def test_preserves_decimal_values(self):
        record = MonthlyRecord(
            "2026-01",
            Decimal("12345.6789"),
            Decimal("7654.3211"),
        )
        self.assertEqual(record.revenue, Decimal("12345.6789"))
        self.assertEqual(record.expenses, Decimal("7654.3211"))

    def test_parses_decimal_strings(self):
        record = MonthlyRecord("2026-02", "100.25", "90.10")
        self.assertEqual(record.revenue, Decimal("100.25"))
        self.assertEqual(record.expenses, Decimal("90.10"))

    def test_accepts_zero_values(self):
        record = MonthlyRecord("2026-03", "0", Decimal("0"))
        self.assertEqual(record.revenue, Decimal("0"))
        self.assertEqual(record.expenses, Decimal("0"))

    def test_rejects_negative_amounts(self):
        for field in ("revenue", "expenses"):
            with self.subTest(field=field):
                values = {"revenue": "100", "expenses": "50"}
                values[field] = "-0.01"
                with self.assertRaises(ValueError):
                    MonthlyRecord("2026-01", **values)

    def test_rejects_nonfinite_amounts(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MonthlyRecord("2026-01", value, "10")

    def test_rejects_unsupported_numeric_types(self):
        for value in (100, 100.0, True, None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    MonthlyRecord("2026-01", value, "10")

    def test_rejects_invalid_amount_strings(self):
        for value in ("", "  ", "invalid", "12x"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MonthlyRecord("2026-01", value, "10")

    def test_is_immutable(self):
        record = MonthlyRecord("2026-01", "100", "50")
        with self.assertRaises(FrozenInstanceError):
            record.revenue = Decimal("999")


class PeriodValidationTests(unittest.TestCase):

    def test_accepts_valid_period_boundaries(self):
        for period in ("0001-01", "2026-12", "9999-06"):
            with self.subTest(period=period):
                self.assertEqual(validate_period(period), period)

    def test_rejects_invalid_months(self):
        for period in ("2026-00", "2026-13", "2026-99"):
            with self.subTest(period=period):
                with self.assertRaises(ValueError):
                    validate_period(period)

    def test_rejects_malformed_periods(self):
        for period in (
            "2026-1",
            "26-01",
            "2026/01",
            "2026-01-01",
            " 2026-01",
            "2026-01 ",
            "abcd-01",
        ):
            with self.subTest(period=period):
                with self.assertRaises(ValueError):
                    validate_period(period)

    def test_rejects_year_zero(self):
        with self.assertRaises(ValueError):
            validate_period("0000-01")

    def test_rejects_non_string_periods(self):
        for value in (202601, None, True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    validate_period(value)


class ScenarioTests(unittest.TestCase):

    def test_parses_decimal_multipliers(self):
        scenario = Scenario("base", "1.00", Decimal("1.10"))
        self.assertEqual(
            scenario.revenue_multiplier,
            Decimal("1.00"),
        )
        self.assertEqual(
            scenario.expense_multiplier,
            Decimal("1.10"),
        )

    def test_trims_scenario_name(self):
        scenario = Scenario("  downside  ", "0.90", "1.10")
        self.assertEqual(scenario.name, "downside")

    def test_allows_zero_multipliers(self):
        scenario = Scenario("zero", "0", "0")
        self.assertEqual(scenario.revenue_multiplier, Decimal("0"))
        self.assertEqual(scenario.expense_multiplier, Decimal("0"))

    def test_rejects_blank_name(self):
        for name in ("", "   "):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Scenario(name, "1", "1")

    def test_rejects_invalid_name_type(self):
        for name in (None, 123, True):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Scenario(name, "1", "1")

    def test_rejects_negative_multipliers(self):
        for revenue, expenses in (
            ("-0.1", "1"),
            ("1", "-0.1"),
        ):
            with self.subTest(revenue=revenue, expenses=expenses):
                with self.assertRaises(ValueError):
                    Scenario("test", revenue, expenses)

    def test_rejects_nonfinite_multipliers(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Scenario("test", value, "1")

    def test_rejects_float_multipliers(self):
        with self.assertRaises(TypeError):
            Scenario("test", 1.0, "1")

    def test_is_immutable(self):
        scenario = Scenario("base", "1", "1")
        with self.assertRaises(FrozenInstanceError):
            scenario.name = "changed"


if __name__ == "__main__":
    unittest.main()
