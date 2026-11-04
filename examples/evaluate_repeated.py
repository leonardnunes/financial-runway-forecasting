"""Repeated reproducible evaluation on synthetic cash-flow regimes."""

from decimal import Decimal
from random import Random

from financial_runway_forecasting.backtest import backtest_cash_flow
from financial_runway_forecasting.models import MonthlyRecord


SEED = 20261105
TRIALS = 100
MONTHS = 24
WINDOW = 6


def build_records(net_flows):
    """Convert synthetic net flows into valid financial observations."""
    return [
        MonthlyRecord(
            period=f"{2024 + index // 12:04d}-{index % 12 + 1:02d}",
            revenue=str(1000 + net_flow),
            expenses="1000",
        )
        for index, net_flow in enumerate(net_flows)
    ]


def generate_case(case, generator):
    """Generate one synthetic cash-flow history."""
    if case == "Stationary variation":
        return [
            generator.randint(-100, 100)
            for _ in range(MONTHS)
        ]

    if case == "Increasing trend":
        return [
            10 + 5 * index + generator.randint(-15, 15)
            for index in range(MONTHS)
        ]

    if case == "Alternating variation":
        return [
            (-100 if index % 2 == 0 else 100)
            + generator.randint(-20, 20)
            for index in range(MONTHS)
        ]

    if case == "Structural break":
        break_index = generator.randint(9, 15)

        return [
            (30 if index < break_index else -90)
            + generator.randint(-15, 15)
            for index in range(MONTHS)
        ]

    raise ValueError(f"Unsupported synthetic case: {case}")


def evaluate_case(case, case_index):
    """Aggregate paired MAE comparisons across independent trials."""
    model_total = Decimal(0)
    naive_total = Decimal(0)

    model_wins = 0
    naive_wins = 0
    ties = 0

    for trial in range(TRIALS):
        generator = Random(
            SEED + case_index * 100000 + trial
        )

        net_flows = generate_case(case, generator)

        evaluation = backtest_cash_flow(
            build_records(net_flows),
            window=WINDOW,
        )

        model_total += evaluation.model_mae
        naive_total += evaluation.naive_mae

        if evaluation.model_mae < evaluation.naive_mae:
            model_wins += 1
        elif evaluation.model_mae > evaluation.naive_mae:
            naive_wins += 1
        else:
            ties += 1

    return (
        model_total / Decimal(TRIALS),
        naive_total / Decimal(TRIALS),
        model_wins,
        naive_wins,
        ties,
    )


def main():
    cases = (
        "Stationary variation",
        "Increasing trend",
        "Alternating variation",
        "Structural break",
    )

    print("REPEATED SYNTHETIC BACKTEST")
    print(f"Base seed: {SEED}")
    print(f"Trials per behavior: {TRIALS}")
    print(f"Months per series: {MONTHS}")
    print(f"Training window: {WINDOW}")
    print(f"Evaluated months per series: {MONTHS - WINDOW}")
    print(f"Total synthetic series: {TRIALS * len(cases)}")
    print()

    for case_index, case in enumerate(cases):
        (
            model_mae,
            naive_mae,
            model_wins,
            naive_wins,
            ties,
        ) = evaluate_case(case, case_index)

        print(case)
        print(f"  Mean trailing-mean MAE: {model_mae:.2f}")
        print(f"  Mean naive-baseline MAE: {naive_mae:.2f}")
        print(f"  Trailing-mean wins: {model_wins}")
        print(f"  Naive-baseline wins: {naive_wins}")
        print(f"  Ties: {ties}")
        print()

    print("Synthetic experiments only.")
    print("No claims about real-world predictive accuracy.")


if __name__ == "__main__":
    main()
