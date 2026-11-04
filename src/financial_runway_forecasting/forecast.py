"""Deterministic cash-flow and financial runway forecasting."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import (
    Context,
    Decimal,
    MAX_EMAX,
    MIN_EMIN,
    ROUND_HALF_EVEN,
    localcontext,
)

from financial_runway_forecasting.models import (
    MonthlyRecord,
    Scenario,
    parse_nonnegative_decimal,
)


DEFAULT_SCENARIOS = (
    Scenario("base", "1.00", "1.00"),
    Scenario("downside", "0.90", "1.10"),
    Scenario("upside", "1.10", "0.95"),
)


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """Projected financial values for one calendar month."""

    period: str
    revenue: Decimal
    expenses: Decimal
    net_cash_flow: Decimal
    closing_cash: Decimal


@dataclass(frozen=True, slots=True)
class ScenarioForecast:
    """Projection and runway estimates for one scenario."""

    scenario: Scenario
    monthly_revenue: Decimal
    monthly_expenses: Decimal
    monthly_net_cash_flow: Decimal
    monthly_burn: Decimal
    runway_months: Decimal | None
    points: tuple[ForecastPoint, ...]


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Complete result of a deterministic financial forecast."""

    historical_count: int
    trailing_window: int
    forecast_horizon: int
    starting_cash: Decimal
    mean_revenue: Decimal
    mean_expenses: Decimal
    scenarios: tuple[ScenarioForecast, ...]


def _month_index(period: str) -> int:
    """Convert YYYY-MM into a monotonically increasing month index."""
    year = int(period[:4])
    month = int(period[5:])
    return year * 12 + month - 1


def _period_from_index(index: int) -> str:
    """Convert a month index back to its canonical YYYY-MM value."""
    year, month_zero_based = divmod(index, 12)

    if not 1 <= year <= 9999:
        raise ValueError(
            "Forecast period exceeds the supported calendar range."
        )

    return f"{year:04d}-{month_zero_based + 1:02d}"


def _validate_history(
    records: Sequence[MonthlyRecord],
) -> tuple[MonthlyRecord, ...]:
    """Validate history types, length, order, and continuity."""
    if isinstance(records, (str, bytes)) or not isinstance(
        records, Sequence
    ):
        raise TypeError("records must be a sequence of MonthlyRecord.")

    observations = tuple(records)

    if len(observations) < 3:
        raise ValueError(
            "At least three historical monthly records are required."
        )

    for index, record in enumerate(observations):
        if not isinstance(record, MonthlyRecord):
            raise TypeError(
                f"Record at index {index} must be a MonthlyRecord."
            )

    for index in range(1, len(observations)):
        previous = _month_index(observations[index - 1].period)
        current = _month_index(observations[index].period)

        if current != previous + 1:
            raise ValueError(
                "Historical periods must be ordered, unique, "
                "and consecutive."
            )

    return observations


def _validate_scenarios(
    scenarios: Sequence[Scenario] | None,
) -> tuple[Scenario, ...]:
    """Validate scenario collection and prevent ambiguous names."""
    if scenarios is None:
        return DEFAULT_SCENARIOS

    if isinstance(scenarios, (str, bytes)) or not isinstance(
        scenarios, Sequence
    ):
        raise TypeError("scenarios must be a sequence of Scenario.")

    selected = tuple(scenarios)

    if not selected:
        raise ValueError("At least one scenario is required.")

    names: set[str] = set()

    for scenario in selected:
        if not isinstance(scenario, Scenario):
            raise TypeError("Each scenario must be a Scenario.")

        normalized_name = scenario.name.casefold()

        if normalized_name in names:
            raise ValueError("Scenario names must be unique.")

        names.add(normalized_name)

    return selected


def _calculation_context(
    amounts: Sequence[Decimal],
) -> Context:
    """Use an isolated, magnitude-aware decimal arithmetic context."""
    largest_adjusted = max(
        (amount.adjusted() for amount in amounts if amount != 0),
        default=0,
    )

    smallest_exponent = min(
        amount.as_tuple().exponent for amount in amounts
    )

    largest_coefficient = max(
        len(amount.as_tuple().digits) for amount in amounts
    )

    precision = max(
        50,
        largest_adjusted - smallest_exponent + 40,
        largest_coefficient + 40,
    )

    return Context(
        prec=precision,
        rounding=ROUND_HALF_EVEN,
        Emin=MIN_EMIN,
        Emax=MAX_EMAX,
    )


def forecast_runway(
    records: Sequence[MonthlyRecord],
    starting_cash: Decimal | str,
    horizon: int = 12,
    window: int | None = None,
    scenarios: Sequence[Scenario] | None = None,
) -> ForecastResult:
    """Forecast monthly cash balances and scenario-based runway.

    This model assumes constant monthly scenario cash flow.

    A None runway means no projected cash depletion under the
    selected scenario, not an infinite real-world survival guarantee.
    """
    observations = _validate_history(records)

    cash = parse_nonnegative_decimal(
        starting_cash,
        "starting_cash",
    )

    if type(horizon) is not int or not 1 <= horizon <= 1200:
        raise ValueError(
            "horizon must be an integer between 1 and 1200."
        )

    if window is None:
        selected_window = min(6, len(observations))
    elif type(window) is not int or not 3 <= window <= len(
        observations
    ):
        raise ValueError(
            "window must be an integer between 3 "
            "and the historical record count."
        )
    else:
        selected_window = window

    selected_scenarios = _validate_scenarios(scenarios)

    final_month = _month_index(observations[-1].period)

    forecast_periods = tuple(
        _period_from_index(final_month + step)
        for step in range(1, horizon + 1)
    )

    trailing_records = observations[-selected_window:]

    amounts = [
        cash,
        *(record.revenue for record in trailing_records),
        *(record.expenses for record in trailing_records),
        *(
            scenario.revenue_multiplier
            for scenario in selected_scenarios
        ),
        *(
            scenario.expense_multiplier
            for scenario in selected_scenarios
        ),
    ]

    with localcontext(_calculation_context(amounts)):
        divisor = Decimal(selected_window)

        mean_revenue = sum(
            (record.revenue for record in trailing_records),
            Decimal(0),
        ) / divisor

        mean_expenses = sum(
            (record.expenses for record in trailing_records),
            Decimal(0),
        ) / divisor

        forecasts = []

        for scenario in selected_scenarios:
            projected_revenue = (
                mean_revenue * scenario.revenue_multiplier
            )

            projected_expenses = (
                mean_expenses * scenario.expense_multiplier
            )

            net_cash_flow = projected_revenue - projected_expenses

            burn = max(-net_cash_flow, Decimal(0))

            if cash == 0:
                runway = Decimal(0)
            elif burn > 0:
                runway = cash / burn
            else:
                runway = None

            points = tuple(
                ForecastPoint(
                    period=period,
                    revenue=projected_revenue,
                    expenses=projected_expenses,
                    net_cash_flow=net_cash_flow,
                    closing_cash=cash + Decimal(step) * net_cash_flow,
                )
                for step, period in enumerate(
                    forecast_periods,
                    start=1,
                )
            )

            forecasts.append(
                ScenarioForecast(
                    scenario=scenario,
                    monthly_revenue=projected_revenue,
                    monthly_expenses=projected_expenses,
                    monthly_net_cash_flow=net_cash_flow,
                    monthly_burn=burn,
                    runway_months=runway,
                    points=points,
                )
            )

        return ForecastResult(
            historical_count=len(observations),
            trailing_window=selected_window,
            forecast_horizon=horizon,
            starting_cash=cash,
            mean_revenue=mean_revenue,
            mean_expenses=mean_expenses,
            scenarios=tuple(forecasts),
        )
