"""Unit tests for rolling-origin financial backtesting."""

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, localcontext

from financial_runway_forecasting.backtest import (
    BacktestPoint,
    BacktestResult,
    backtest_cash_flow,
)
from financial_runway_forecasting.models import MonthlyRecord


def increasing_history():
    """Five months with net cash flows of 10, 20, 30, 40, 50."""
    revenues = ("100", "120", "140", "160", "180")
    expenses = ("90", "100", "110", "120", "130")

    return [
        MonthlyRecord(f"2026-{month:02d}", revenue, expense)
        for month, (revenue, expense) in enumerate(
            zip(revenues, expenses),
            start=1,
        )
    ]


def history_from_net_flows(values):
    """Create synthetic observations from nonnegative net inflows."""
    return [
        MonthlyRecord(f"2026-{month:02d}", str(value), "0")
        for month, value in enumerate(values, start=1)
    ]


class BacktestCalculationTests(unittest.TestCase):

    def test_result_structure(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.historical_count, 5)
        self.assertEqual(result.trailing_window, 3)
        self.assertEqual(result.evaluation_count, 2)
        self.assertEqual(len(result.points), 2)
        self.assertIsInstance(result.points[0], BacktestPoint)

    def test_first_forecast_uses_prior_three_months(self):
        result = backtest_cash_flow(increasing_history(), window=3)
        point = result.points[0]

        self.assertEqual(point.origin_period, "2026-03")
        self.assertEqual(point.target_period, "2026-04")
        self.assertEqual(
            point.predicted_net_cash_flow,
            Decimal("20"),
        )
        self.assertEqual(
            point.actual_net_cash_flow,
            Decimal("40"),
        )

    def test_second_forecast_advances_training_window(self):
        result = backtest_cash_flow(increasing_history(), window=3)
        point = result.points[1]

        self.assertEqual(point.origin_period, "2026-04")
        self.assertEqual(point.target_period, "2026-05")
        self.assertEqual(
            point.predicted_net_cash_flow,
            Decimal("30"),
        )
        self.assertEqual(
            point.actual_net_cash_flow,
            Decimal("50"),
        )

    def test_naive_baseline_uses_previous_month(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        self.assertEqual(
            [
                point.naive_predicted_net_cash_flow
                for point in result.points
            ],
            [Decimal("30"), Decimal("40")],
        )

    def test_errors_are_prediction_minus_actual(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        self.assertEqual(
            [point.model_error for point in result.points],
            [Decimal("-20"), Decimal("-20")],
        )
        self.assertEqual(
            [point.naive_error for point in result.points],
            [Decimal("-10"), Decimal("-10")],
        )

    def test_mae_and_bias_are_correct(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        self.assertEqual(result.model_mae, Decimal("20"))
        self.assertEqual(result.model_bias, Decimal("-20"))
        self.assertEqual(result.naive_mae, Decimal("10"))
        self.assertEqual(result.naive_bias, Decimal("-10"))

    def test_naive_baseline_can_outperform_model(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        self.assertLess(result.naive_mae, result.model_mae)

    def test_trailing_mean_can_outperform_naive(self):
        records = history_from_net_flows(
            (0, 100, 0, 100, 0, 100)
        )
        result = backtest_cash_flow(records, window=3)

        self.assertLess(result.model_mae, result.naive_mae)

    def test_constant_cash_flow_has_zero_error(self):
        records = history_from_net_flows((25, 25, 25, 25, 25))
        result = backtest_cash_flow(records, window=3)

        self.assertEqual(result.model_mae, Decimal("0"))
        self.assertEqual(result.model_bias, Decimal("0"))
        self.assertEqual(result.naive_mae, Decimal("0"))
        self.assertEqual(result.naive_bias, Decimal("0"))

    def test_future_target_does_not_change_earlier_prediction(self):
        records = increasing_history()
        original = backtest_cash_flow(records, window=3)

        changed = list(records)
        changed[3] = MonthlyRecord("2026-04", "900", "100")
        modified = backtest_cash_flow(changed, window=3)

        self.assertEqual(
            original.points[0].predicted_net_cash_flow,
            modified.points[0].predicted_net_cash_flow,
        )
        self.assertNotEqual(
            original.points[0].actual_net_cash_flow,
            modified.points[0].actual_net_cash_flow,
        )

    def test_default_window_uses_six_months(self):
        records = history_from_net_flows(range(10, 90, 10))
        result = backtest_cash_flow(records)

        self.assertEqual(result.historical_count, 8)
        self.assertEqual(result.trailing_window, 6)
        self.assertEqual(result.evaluation_count, 2)

    def test_custom_window_changes_evaluation_count(self):
        records = history_from_net_flows(range(10, 90, 10))
        result = backtest_cash_flow(records, window=3)

        self.assertEqual(result.trailing_window, 3)
        self.assertEqual(result.evaluation_count, 5)

    def test_minimum_valid_history(self):
        records = history_from_net_flows((10, 20, 30, 40))
        result = backtest_cash_flow(records)

        self.assertEqual(result.trailing_window, 3)
        self.assertEqual(result.evaluation_count, 1)

    def test_decimal_fractional_values_are_preserved(self):
        records = history_from_net_flows(
            ("0.001", "0.002", "0.003", "0.004")
        )
        result = backtest_cash_flow(records, window=3)

        self.assertEqual(
            result.points[0].predicted_net_cash_flow,
            Decimal("0.002"),
        )
        self.assertEqual(
            result.points[0].model_error,
            Decimal("-0.002"),
        )

    def test_external_decimal_context_does_not_change_results(self):
        records = [
            MonthlyRecord(
                f"2026-{month:02d}",
                "12345.67890123456789",
                "9876.54321098765432",
            )
            for month in range(1, 6)
        ]

        expected = backtest_cash_flow(records, window=3)

        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            actual = backtest_cash_flow(records, window=3)

        self.assertEqual(actual, expected)

    def test_repeated_evaluations_are_deterministic(self):
        records = increasing_history()

        self.assertEqual(
            backtest_cash_flow(records, window=3),
            backtest_cash_flow(records, window=3),
        )

    def test_result_objects_are_immutable(self):
        result = backtest_cash_flow(increasing_history(), window=3)

        with self.assertRaises(FrozenInstanceError):
            result.model_mae = Decimal("999")

        with self.assertRaises(FrozenInstanceError):
            result.points[0].model_error = Decimal("999")


class BacktestValidationTests(unittest.TestCase):

    def test_rejects_insufficient_history(self):
        for count in (0, 1, 2, 3):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    backtest_cash_flow(increasing_history()[:count])

    def test_rejects_invalid_window(self):
        records = increasing_history()

        for value in (0, 1, 2, 5, 6, -1, True, 3.0, "3"):
            with self.subTest(window=value):
                with self.assertRaises(ValueError):
                    backtest_cash_flow(records, window=value)

    def test_rejects_duplicate_months(self):
        records = increasing_history()
        records[2] = MonthlyRecord("2026-02", "140", "110")

        with self.assertRaises(ValueError):
            backtest_cash_flow(records, window=3)

    def test_rejects_missing_months(self):
        records = increasing_history()
        records[3] = MonthlyRecord("2026-06", "160", "120")

        with self.assertRaises(ValueError):
            backtest_cash_flow(records, window=3)

    def test_rejects_unsorted_history(self):
        with self.assertRaises(ValueError):
            backtest_cash_flow(
                list(reversed(increasing_history())),
                window=3,
            )

    def test_rejects_invalid_record_type(self):
        records = increasing_history()
        records[1] = "not a record"

        with self.assertRaises(TypeError):
            backtest_cash_flow(records, window=3)

    def test_accepts_tuple_history(self):
        result = backtest_cash_flow(
            tuple(increasing_history()),
            window=3,
        )
        self.assertEqual(result.evaluation_count, 2)

    def test_rejects_generator_history(self):
        records = (record for record in increasing_history())

        with self.assertRaises(TypeError):
            backtest_cash_flow(records, window=3)


if __name__ == "__main__":
    unittest.main()
