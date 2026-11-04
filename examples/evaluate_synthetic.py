"""Reproducible synthetic comparison of cash-flow forecasting baselines."""

from decimal import Decimal
from random import Random

from financial_runway_forecasting.backtest import backtest_cash_flow
from financial_runway_forecasting.models import MonthlyRecord


SEED = 20261104
WINDOW = 6
MONTHS = 24


def make_history(net_flows: list[int]) -> list[MonthlyRecord]:
    """Construct synthetic monthly data from specified net cash flows."""
    records = []

    for index, net_flow in enumerate(net_flows):
        year = 2024 + index // 12
        month = index % 12 + 1

        records.append(
            MonthlyRecord(
                period=f"{year:04d}-{month:02d}",
                revenue=str(1000 + net_flow),
                expenses="1000",
            )
        )

    return records


def synthetic_cases() -> dict[str, list[int]]:
    """Provide fixed synthetic financial patterns for evaluation."""
    generator = Random(SEED)

    return {
        "Constant cash flow": [
            20 for _ in range(MONTHS)
        ],
        "Increasing trend": [
            10 + 5 * index for index in range(MONTHS)
        ],
        "Alternating cash flow": [
            100 if index % 2 else -100
            for index in range(MONTHS)
        ],
        "Structural break": [
            30 if index < 12 else -90
            for index in range(MONTHS)
        ],
        "Seeded random variation": [
            generator.randint(-100, 100)
            for _ in range(MONTHS)
        ],
    }


def format_money(value: Decimal) -> str:
    """Format metrics for display without changing stored precision."""
    return f"{value:.2f}"


def main() -> None:
    print("SYNTHETIC CASH-FLOW BACKTEST")
    print(f"Seed: {SEED}")
    print(f"Historical months per case: {MONTHS}")
    print(f"Trailing window: {WINDOW}")
    print("Evaluation: rolling-origin, one-step-ahead")
    print("Error definition: predicted minus actual")
    print()

    for name, net_flows in synthetic_cases().items():
        records = make_history(net_flows)
        result = backtest_cash_flow(records, window=WINDOW)

        if result.model_mae < result.naive_mae:
            winner = "Trailing mean"
        elif result.model_mae > result.naive_mae:
            winner = "Naive baseline"
        else:
            winner = "Tie"

        print(name)
        print(f"  Evaluated months: {result.evaluation_count}")
        print(f"  Trailing-mean MAE: {format_money(result.model_mae)}")
        print(f"  Naive-baseline MAE: {format_money(result.naive_mae)}")
        print(f"  Trailing-mean bias: {format_money(result.model_bias)}")
        print(f"  Naive-baseline bias: {format_money(result.naive_bias)}")
        print(f"  Lower MAE: {winner}")
        print()

    print("All data are synthetic.")
    print("No real-world forecasting accuracy is implied.")


if __name__ == "__main__":
    main()
