"""End-to-end example using entirely synthetic company finances."""

from financial_runway_forecasting.backtest import backtest_cash_flow
from financial_runway_forecasting.forecast import forecast_runway
from financial_runway_forecasting.models import MonthlyRecord


SYNTHETIC_DATA = [
    ("2025-01", "18500", "22000"),
    ("2025-02", "19200", "22500"),
    ("2025-03", "18100", "21900"),
    ("2025-04", "19800", "23100"),
    ("2025-05", "19000", "22400"),
    ("2025-06", "20100", "23500"),
    ("2025-07", "19500", "22900"),
    ("2025-08", "18700", "23700"),
    ("2025-09", "20300", "23400"),
    ("2025-10", "19600", "24100"),
    ("2025-11", "21000", "24300"),
    ("2025-12", "19700", "23900"),
]


def main() -> None:
    records = [
        MonthlyRecord(period, revenue, expenses)
        for period, revenue, expenses in SYNTHETIC_DATA
    ]

    forecast = forecast_runway(
        records,
        starting_cash="25000",
        horizon=6,
        window=6,
    )

    print("FINANCIAL RUNWAY FORECASTING")
    print("Synthetic demonstration — monetary units unspecified")
    print()
    print(f"Historical months: {forecast.historical_count}")
    print(f"Trailing window: {forecast.trailing_window}")
    print(f"Starting cash: {forecast.starting_cash:,.2f}")
    print(f"Mean monthly revenue: {forecast.mean_revenue:,.2f}")
    print(f"Mean monthly expenses: {forecast.mean_expenses:,.2f}")
    print()

    for scenario in forecast.scenarios:
        print(f"SCENARIO: {scenario.scenario.name}")
        print(f"  Monthly net flow: {scenario.monthly_net_cash_flow:,.2f}")
        print(f"  Monthly burn: {scenario.monthly_burn:,.2f}")

        if scenario.runway_months is None:
            print("  Runway: no depletion under constant-flow assumptions")
        else:
            print(f"  Estimated runway: {scenario.runway_months:.2f} months")

        print("  Projected closing cash:")
        for point in scenario.points:
            print(f"    {point.period}: {point.closing_cash:,.2f}")

        print()

    evaluation = backtest_cash_flow(records, window=6)

    print("HISTORICAL ONE-STEP BACKTEST")
    print(f"Evaluated months: {evaluation.evaluation_count}")
    print(f"Trailing-mean MAE: {evaluation.model_mae:,.2f}")
    print(f"Naive-baseline MAE: {evaluation.naive_mae:,.2f}")
    print(f"Trailing-mean bias: {evaluation.model_bias:,.2f}")
    print(f"Naive-baseline bias: {evaluation.naive_bias:,.2f}")
    print()
    print("All observations are synthetic.")
    print("Forecasts are illustrative, not financial advice.")


if __name__ == "__main__":
    main()
