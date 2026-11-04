"""Tests for deterministic financial runway forecasting."""

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, localcontext

from financial_runway_forecasting.forecast import (
    ForecastResult,
    ScenarioForecast,
    forecast_runway,
)
from financial_runway_forecasting.models import MonthlyRecord, Scenario


def sample_history():
    return [
        MonthlyRecord("2026-01", "100", "150"),
        MonthlyRecord("2026-02", "100", "150"),
        MonthlyRecord("2026-03", "100", "150"),
    ]


class ForecastCalculationTests(unittest.TestCase):

    def test_result_structure(self):
        result = forecast_runway(sample_history(), "120")
        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(result.historical_count, 3)
        self.assertEqual(result.trailing_window, 3)
        self.assertEqual(result.forecast_horizon, 12)
        self.assertEqual(len(result.scenarios), 3)

    def test_base_scenario(self):
        result = forecast_runway(sample_history(), "120", horizon=3)
        base = result.scenarios[0]

        self.assertIsInstance(base, ScenarioForecast)
        self.assertEqual(base.scenario.name, "base")
        self.assertEqual(base.monthly_revenue, Decimal("100"))
        self.assertEqual(base.monthly_expenses, Decimal("150"))
        self.assertEqual(base.monthly_net_cash_flow, Decimal("-50"))
        self.assertEqual(base.monthly_burn, Decimal("50"))
        self.assertEqual(base.runway_months, Decimal("2.4"))

        self.assertEqual(
            [point.closing_cash for point in base.points],
            [Decimal("70"), Decimal("20"), Decimal("-30")],
        )

    def test_downside_scenario(self):
        result = forecast_runway(sample_history(), "120", horizon=1)
        downside = result.scenarios[1]

        self.assertEqual(downside.scenario.name, "downside")
        self.assertEqual(downside.monthly_revenue, Decimal("90"))
        self.assertEqual(downside.monthly_expenses, Decimal("165"))
        self.assertEqual(downside.monthly_net_cash_flow, Decimal("-75"))
        self.assertEqual(downside.runway_months, Decimal("1.6"))
        self.assertEqual(downside.points[0].closing_cash, Decimal("45"))

    def test_upside_scenario(self):
        result = forecast_runway(sample_history(), "120", horizon=1)
        upside = result.scenarios[2]

        self.assertEqual(upside.scenario.name, "upside")
        self.assertEqual(upside.monthly_revenue, Decimal("110"))
        self.assertEqual(upside.monthly_expenses, Decimal("142.50"))
        self.assertEqual(upside.monthly_net_cash_flow, Decimal("-32.50"))
        self.assertEqual(upside.monthly_burn, Decimal("32.50"))
        self.assertEqual(upside.points[0].closing_cash, Decimal("87.50"))

    def test_profitable_operation_has_no_finite_runway(self):
        records = [
            MonthlyRecord("2026-01", "200", "100"),
            MonthlyRecord("2026-02", "200", "100"),
            MonthlyRecord("2026-03", "200", "100"),
        ]
        result = forecast_runway(records, "500", horizon=2)
        base = result.scenarios[0]

        self.assertEqual(base.monthly_burn, Decimal(0))
        self.assertIsNone(base.runway_months)
        self.assertEqual(base.points[-1].closing_cash, Decimal("700"))

    def test_zero_initial_cash_has_zero_runway(self):
        result = forecast_runway(sample_history(), "0")
        self.assertTrue(
            all(
                scenario.runway_months == Decimal(0)
                for scenario in result.scenarios
            )
        )

    def test_zero_cash_flow(self):
        records = [
            MonthlyRecord("2026-01", "100", "100"),
            MonthlyRecord("2026-02", "100", "100"),
            MonthlyRecord("2026-03", "100", "100"),
        ]
        result = forecast_runway(records, "300", horizon=2)
        base = result.scenarios[0]

        self.assertEqual(base.monthly_net_cash_flow, Decimal(0))
        self.assertEqual(base.monthly_burn, Decimal(0))
        self.assertIsNone(base.runway_months)
        self.assertEqual(base.points[-1].closing_cash, Decimal("300"))

    def test_negative_projected_balances_are_preserved(self):
        result = forecast_runway(sample_history(), "10", horizon=2)
        base = result.scenarios[0]

        self.assertEqual(base.points[0].closing_cash, Decimal("-40"))
        self.assertEqual(base.points[1].closing_cash, Decimal("-90"))

    def test_forecast_periods_are_consecutive(self):
        result = forecast_runway(sample_history(), "120", horizon=3)
        periods = [point.period for point in result.scenarios[0].points]

        self.assertEqual(
            periods,
            ["2026-04", "2026-05", "2026-06"],
        )

    def test_december_to_january_transition(self):
        records = [
            MonthlyRecord("2026-10", "100", "150"),
            MonthlyRecord("2026-11", "100", "150"),
            MonthlyRecord("2026-12", "100", "150"),
        ]
        result = forecast_runway(records, "200", horizon=2)

        self.assertEqual(
            [point.period for point in result.scenarios[0].points],
            ["2027-01", "2027-02"],
        )

    def test_calendar_overflow_is_rejected(self):
        records = [
            MonthlyRecord("9999-10", "100", "150"),
            MonthlyRecord("9999-11", "100", "150"),
            MonthlyRecord("9999-12", "100", "150"),
        ]

        with self.assertRaises(ValueError):
            forecast_runway(records, "100", horizon=1)

    def test_custom_trailing_window(self):
        records = [
            MonthlyRecord("2026-01", "100", "50"),
            MonthlyRecord("2026-02", "200", "60"),
            MonthlyRecord("2026-03", "300", "70"),
            MonthlyRecord("2026-04", "400", "80"),
        ]
        result = forecast_runway(records, "1000", window=3)

        self.assertEqual(result.trailing_window, 3)
        self.assertEqual(result.mean_revenue, Decimal("300"))
        self.assertEqual(result.mean_expenses, Decimal("70"))

    def test_default_window_uses_at_most_six_months(self):
        records = [
            MonthlyRecord(f"2026-{month:02d}", str(month * 10), "5")
            for month in range(1, 8)
        ]
        result = forecast_runway(records, "100")

        self.assertEqual(result.trailing_window, 6)
        self.assertEqual(result.mean_revenue, Decimal("45"))
        self.assertEqual(result.mean_expenses, Decimal("5"))

    def test_custom_scenario(self):
        custom = Scenario("stress", "0.50", "2.00")
        result = forecast_runway(
            sample_history(),
            "300",
            horizon=1,
            scenarios=[custom],
        )

        self.assertEqual(len(result.scenarios), 1)
        stress = result.scenarios[0]
        self.assertEqual(stress.scenario.name, "stress")
        self.assertEqual(stress.monthly_revenue, Decimal("50"))
        self.assertEqual(stress.monthly_expenses, Decimal("300"))
        self.assertEqual(stress.monthly_net_cash_flow, Decimal("-250"))
        self.assertEqual(stress.runway_months, Decimal("1.2"))

    def test_fractional_money_is_not_rounded_to_cents(self):
        records = [
            MonthlyRecord("2026-01", "0.001", "0.002"),
            MonthlyRecord("2026-02", "0.001", "0.002"),
            MonthlyRecord("2026-03", "0.001", "0.002"),
        ]
        result = forecast_runway(records, "1.000", horizon=3)
        base = result.scenarios[0]

        self.assertEqual(base.monthly_net_cash_flow, Decimal("-0.001"))
        self.assertEqual(base.points[-1].closing_cash, Decimal("0.997"))
        self.assertEqual(base.runway_months, Decimal("1000"))

    def test_external_decimal_precision_does_not_change_result(self):
        records = [
            MonthlyRecord("2026-01", "12345.678901", "9876.543210"),
            MonthlyRecord("2026-02", "12345.678901", "9876.543210"),
            MonthlyRecord("2026-03", "12345.678901", "9876.543210"),
        ]
        expected = forecast_runway(records, "10000", horizon=3)

        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            actual = forecast_runway(records, "10000", horizon=3)

        self.assertEqual(actual, expected)

    def test_repeated_calls_are_deterministic(self):
        first = forecast_runway(sample_history(), "120")
        second = forecast_runway(sample_history(), "120")
        self.assertEqual(first, second)

    def test_results_are_immutable(self):
        result = forecast_runway(sample_history(), "120")

        with self.assertRaises(FrozenInstanceError):
            result.starting_cash = Decimal("999")

        with self.assertRaises(FrozenInstanceError):
            result.scenarios[0].monthly_burn = Decimal("999")


class ForecastValidationTests(unittest.TestCase):

    def test_rejects_insufficient_history(self):
        with self.assertRaises(ValueError):
            forecast_runway(sample_history()[:2], "100")

    def test_rejects_duplicate_month(self):
        records = sample_history()
        records[2] = MonthlyRecord("2026-02", "100", "150")

        with self.assertRaises(ValueError):
            forecast_runway(records, "100")

    def test_rejects_missing_month(self):
        records = sample_history()
        records[2] = MonthlyRecord("2026-04", "100", "150")

        with self.assertRaises(ValueError):
            forecast_runway(records, "100")

    def test_rejects_unsorted_history(self):
        records = list(reversed(sample_history()))

        with self.assertRaises(ValueError):
            forecast_runway(records, "100")

    def test_rejects_invalid_record_type(self):
        records = sample_history()
        records[1] = "invalid"

        with self.assertRaises(TypeError):
            forecast_runway(records, "100")

    def test_rejects_generator_history(self):
        records = (record for record in sample_history())

        with self.assertRaises(TypeError):
            forecast_runway(records, "100")

    def test_rejects_invalid_starting_cash(self):
        for value in ("-1", "NaN", "Infinity", "invalid"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    forecast_runway(sample_history(), value)

        for value in (100, 100.0, None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    forecast_runway(sample_history(), value)

    def test_rejects_invalid_horizon(self):
        for value in (0, -1, 1201, 1.5, True, "12", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    forecast_runway(
                        sample_history(),
                        "100",
                        horizon=value,
                    )

    def test_rejects_invalid_window(self):
        for value in (0, 2, 4, 1.5, True, "3"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    forecast_runway(
                        sample_history(),
                        "100",
                        window=value,
                    )

    def test_rejects_empty_scenario_collection(self):
        with self.assertRaises(ValueError):
            forecast_runway(
                sample_history(),
                "100",
                scenarios=[],
            )

    def test_rejects_duplicate_scenario_names(self):
        scenarios = [
            Scenario("Base", "1", "1"),
            Scenario("base", "0.9", "1.1"),
        ]

        with self.assertRaises(ValueError):
            forecast_runway(
                sample_history(),
                "100",
                scenarios=scenarios,
            )

    def test_rejects_invalid_scenario_collection(self):
        for scenarios in ("base", [123], [None]):
            with self.subTest(scenarios=scenarios):
                with self.assertRaises(TypeError):
                    forecast_runway(
                        sample_history(),
                        "100",
                        scenarios=scenarios,
                    )


if __name__ == "__main__":
    unittest.main()
