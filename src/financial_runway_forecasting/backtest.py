"""Leakage-free rolling-origin evaluation of monthly cash-flow forecasts."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from financial_runway_forecasting.forecast import (
    _calculation_context,
    _validate_history,
)
from financial_runway_forecasting.models import MonthlyRecord


@dataclass(frozen=True, slots=True)
class BacktestPoint:
    """One out-of-sample, one-step-ahead forecast comparison."""

    origin_period: str
    target_period: str
    predicted_net_cash_flow: Decimal
    actual_net_cash_flow: Decimal
    naive_predicted_net_cash_flow: Decimal
    model_error: Decimal
    naive_error: Decimal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Evaluation metrics for the trailing-mean and naive baselines."""

    historical_count: int
    trailing_window: int
    evaluation_count: int
    model_mae: Decimal
    model_bias: Decimal
    naive_mae: Decimal
    naive_bias: Decimal
    points: tuple[BacktestPoint, ...]


def backtest_cash_flow(
    records: list[MonthlyRecord] | tuple[MonthlyRecord, ...],
    window: int | None = None,
) -> BacktestResult:
    """Evaluate one-month-ahead cash-flow forecasts without future leakage.

    The forecast at each origin uses only the preceding `window`
    observations. Errors are defined as predicted minus actual.

    The naive baseline predicts that the next month's net cash flow
    will equal the immediately preceding month's net cash flow.

    A default evaluation window is min(6, N - 1), where N is the
    number of observations. This ensures at least one test month.
    """
    observations = _validate_history(records)
    count = len(observations)

    if count < 4:
        raise ValueError(
            "At least four monthly records are required for backtesting."
        )

    if window is None:
        selected_window = min(6, count - 1)
    elif type(window) is not int or not 3 <= window < count:
        raise ValueError(
            "window must be an integer between 3 "
            "and historical_count - 1."
        )
    else:
        selected_window = window

    amounts = [
        value
        for record in observations
        for value in (record.revenue, record.expenses)
    ]

    with localcontext(_calculation_context(amounts)):
        points = []
        divisor = Decimal(selected_window)

        for target_index in range(selected_window, count):
            training = observations[
                target_index - selected_window:target_index
            ]

            target = observations[target_index]
            previous = observations[target_index - 1]

            predicted_revenue = sum(
                (record.revenue for record in training),
                Decimal(0),
            ) / divisor

            predicted_expenses = sum(
                (record.expenses for record in training),
                Decimal(0),
            ) / divisor

            predicted_net = predicted_revenue - predicted_expenses
            actual_net = target.revenue - target.expenses
            naive_net = previous.revenue - previous.expenses

            points.append(
                BacktestPoint(
                    origin_period=previous.period,
                    target_period=target.period,
                    predicted_net_cash_flow=predicted_net,
                    actual_net_cash_flow=actual_net,
                    naive_predicted_net_cash_flow=naive_net,
                    model_error=predicted_net - actual_net,
                    naive_error=naive_net - actual_net,
                )
            )

        evaluation_count = len(points)
        evaluation_divisor = Decimal(evaluation_count)

        model_mae = sum(
            (abs(point.model_error) for point in points),
            Decimal(0),
        ) / evaluation_divisor

        model_bias = sum(
            (point.model_error for point in points),
            Decimal(0),
        ) / evaluation_divisor

        naive_mae = sum(
            (abs(point.naive_error) for point in points),
            Decimal(0),
        ) / evaluation_divisor

        naive_bias = sum(
            (point.naive_error for point in points),
            Decimal(0),
        ) / evaluation_divisor

        return BacktestResult(
            historical_count=count,
            trailing_window=selected_window,
            evaluation_count=evaluation_count,
            model_mae=model_mae,
            model_bias=model_bias,
            naive_mae=naive_mae,
            naive_bias=naive_bias,
            points=tuple(points),
        )
