# Financial Runway Forecasting

A reproducible Python project for financial cash-flow forecasting,
scenario analysis, runway estimation, and historical backtesting.

The project demonstrates transparent financial modeling,
defensive input validation, decimal arithmetic, automated testing,
and empirical comparison with a naive forecasting baseline.

All demonstrations and evaluations use synthetic data.

## Features

- Monthly revenue and expense modeling.
- Strict validation of chronological financial records.
- Configurable trailing-mean forecasting.
- Base, downside, and upside scenarios.
- Monthly cash-balance projections.
- Net burn-rate and financial runway estimation.
- Rolling-origin, one-step-ahead backtesting.
- MAE and forecast-bias evaluation.
- Comparison with a previous-month naive baseline.
- Reproducible synthetic experiments.
- Automated unit tests.

## Technologies

- Python 3.13+
- Python standard library
- Decimal arithmetic
- unittest
- Git and GitHub Actions

No third-party runtime dependencies are required.

## Installation

Clone this repository and enter its directory.

Create and activate a Python virtual environment, then install
the package in editable mode.

Windows PowerShell:

    py -3.13 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e .

Run the test suite:

    .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v

On Linux or macOS, use the equivalent Python 3.13 virtual
environment commands.

## Quick Start

Run the complete synthetic financial example:

    .\.venv\Scripts\python.exe -B .\examples\basic_usage.py

The example projects six months of cash balances under three
scenarios and evaluates one-step-ahead forecasting accuracy.

### Python API

    from financial_runway_forecasting.models import MonthlyRecord
    from financial_runway_forecasting.forecast import forecast_runway

    history = [
        MonthlyRecord("2026-01", "100", "150"),
        MonthlyRecord("2026-02", "100", "150"),
        MonthlyRecord("2026-03", "100", "150"),
    ]

    result = forecast_runway(
        history,
        starting_cash="120",
        horizon=3,
    )

    base = result.scenarios[0]

    print(base.monthly_burn)
    print(base.runway_months)

Expected values:

- Monthly burn: 50
- Estimated runway: 2.4 months

Input monetary amounts must be Decimal objects or decimal
strings. Float inputs are intentionally rejected.

## Forecasting Method

The baseline estimates monthly revenue and expenses using
a trailing historical mean.

    expected_revenue = mean(previous monthly revenues)
    expected_expenses = mean(previous monthly expenses)

For scenario multipliers alpha and beta:

    projected_net_flow = alpha * expected_revenue
                         - beta * expected_expenses

Projected closing cash after t months:

    closing_cash(t) = starting_cash + t * projected_net_flow

Monthly net burn:

    burn = max(-projected_net_flow, 0)

For positive starting cash and positive burn:

    runway_months = starting_cash / burn

When the starting cash is positive and projected burn is
zero, runway is reported as None. This does not guarantee
unlimited business survival.

The default trailing window uses up to six historical months,
and the default projection horizon is twelve months.

## Scenario Analysis

The default illustrative scenarios are:

| Scenario | Revenue multiplier | Expense multiplier |
|---|---:|---:|
| Base | 1.00 | 1.00 |
| Downside | 0.90 | 1.10 |
| Upside | 1.10 | 0.95 |

Users may supply custom scenarios.

Scenario multipliers describe assumptions, not probabilities
or statistically calibrated confidence bounds.

## Historical Backtesting

Rolling-origin backtesting generates forecasts using only
observations available before the target month.

Two methods are compared:

1. Trailing mean of historical revenue and expenses.
2. Naive baseline using the previous month's net cash flow.

Evaluation metrics:

- MAE: mean absolute error.
- Bias: mean prediction error, defined as predicted minus actual.

Backtesting evaluates one-month-ahead cash-flow accuracy.
It does not directly validate long-term solvency predictions.

## Experimental Results

The repeated synthetic evaluation includes:

- Four financial behavior regimes.
- 100 independent seeded series per regime.
- 400 synthetic series.
- 7,200 one-month-ahead forecast comparisons.

Average MAE across trials:

| Synthetic behavior | Trailing mean | Naive baseline |
|---|---:|---:|
| Stationary variation | 52.52 | 67.99 |
| Increasing trend | 17.51 | 11.35 |
| Alternating variation | 100.31 | 200.62 |
| Structural break | 28.52 | 16.31 |

The trailing mean performed better in stationary and
alternating examples. The naive baseline performed better
under increasing trends and structural changes.

These outcomes apply to the specified synthetic generators.
They do not establish real-world predictive accuracy.

To reproduce the experiments:

    .\.venv\Scripts\python.exe -B .\examples\evaluate_synthetic.py
    .\.venv\Scripts\python.exe -B .\examples\evaluate_repeated.py

Detailed methodology and results:

- docs/methodology.md
- docs/evaluation.md

## Repository Structure

    financial-runway-forecasting/
        src/
            financial_runway_forecasting/
                __init__.py
                models.py
                forecast.py
                backtest.py
        tests/
            test_models.py
            test_forecast.py
            test_backtest.py
        examples/
            basic_usage.py
            evaluate_synthetic.py
            evaluate_repeated.py
        docs/
            methodology.md
            evaluation.md
        pyproject.toml
        README.md

## Limitations

- Deterministic baseline; not a probabilistic forecast.
- Constant projected monthly cash flow within each scenario.
- No explicit trend, seasonality, or inflation forecasting.
- Sensitive to outliers and structural changes.
- No debt covenants, credit facilities, or financing events.
- No external validation using real financial records.
- No calibrated prediction intervals.
- Negative projected balances are diagnostic, not credit access.
- Fractional runway months assume uniform cash-flow timing.

This software is an educational and analytical demonstration,
not personalized financial advice.

## Data and Privacy

The examples use synthetic financial records.

No confidential business data, credentials, or customer
information are required to run the project.

## Testing and Reproducibility

The project uses Python's unittest framework.

Experiments use fixed pseudorandom seeds and report their
configuration. Historical forecast origins exclude future
observations.

Automated tests validate data types, chronological integrity,
numerical behavior, cash-flow projections, and backtesting.

## Project Status

Research-oriented portfolio implementation with a tested
deterministic forecasting baseline.

The project is not intended to replace financial planning,
professional judgment, or production-grade treasury software.
