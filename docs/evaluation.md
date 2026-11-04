# Experimental Evaluation

## 1. Objective

Evaluate one-step-ahead financial cash-flow forecasts using
synthetic monthly observations.

The project compares a six-month trailing-mean forecast
against a naive previous-month baseline.

All reported results are synthetic and reproducible.
They do not demonstrate accuracy on real-world company data.

## 2. Methods

### Trailing-mean forecast

Expected next-month cash flow equals average revenue minus
average expenses over the preceding six months.

### Naive baseline

Expected next-month cash flow equals the preceding month's
observed net cash flow.

Both methods use information available before the target month.

## 3. Evaluation design

- Historical observations: 24 monthly records per series.
- Initial training window: six months.
- Evaluation: rolling-origin, one month ahead.
- Predictions evaluated per series: 18.
- Error definition: prediction minus actual cash flow.
- Primary metric: mean absolute error (MAE).
- Secondary metric: mean signed error (bias).

Lower MAE indicates lower average absolute forecast error.

## 4. Initial synthetic experiments

Script: examples/evaluate_synthetic.py
Random seed: 20261104.

| Behavior | Trailing-mean MAE | Naive MAE | Winner |
|---|---:|---:|---|
| Constant cash flow | 0.00 | 0.00 | Tie |
| Increasing trend | 17.50 | 5.00 | Naive |
| Alternating cash flow | 100.00 | 200.00 | Trailing mean |
| Structural break | 23.33 | 6.67 | Naive |
| Seeded random variation | 59.90 | 75.61 | Trailing mean |

Each behavior is represented by one illustrative synthetic
series. These initial examples do not establish general
forecasting performance.

## 5. Repeated synthetic experiments

Script: examples/evaluate_repeated.py

Configuration:

- Base random seed: 20261105.
- Four synthetic cash-flow behaviors.
- 100 trials per behavior.
- 400 synthetic series in total.
- 18 evaluated predictions per series.
- 7,200 one-step-ahead predictions in total.

Each trial uses a deterministic random seed. Both methods
are evaluated on the same observations.

Reported MAE values are averages of per-series MAEs.

| Behavior | Trailing MAE | Naive MAE | Trailing wins | Naive wins |
|---|---:|---:|---:|---:|
| Stationary variation | 52.52 | 67.99 | 96 | 4 |
| Increasing trend | 17.51 | 11.35 | 0 | 100 |
| Alternating variation | 100.31 | 200.62 | 100 | 0 |
| Structural break | 28.52 | 16.31 | 0 | 100 |

No ties occurred in the repeated experiments.

Amounts represent unspecified synthetic monetary units.

## 6. Interpretation

### Stationary variation

The trailing mean achieved lower MAE in 96 of 100 trials.
Averaging previous observations reduced sensitivity to
individual fluctuations in this synthetic setting.

### Increasing trend

The naive baseline achieved lower MAE in all 100 trials.
The trailing mean systematically lagged behind the trend.

### Alternating variation

The trailing mean achieved lower MAE in all 100 trials.
The naive baseline repeatedly followed the previous extreme.

### Structural break

The naive baseline achieved lower MAE in all 100 trials.
The trailing mean retained pre-break observations and
adapted more slowly.

These results are conditional on the specified synthetic
data-generation processes.

## 7. Reproduction

Run these commands from the project root using the project's
Python environment:

- .\.venv\Scripts\python.exe -B .\examples\evaluate_synthetic.py
- .\.venv\Scripts\python.exe -B .\examples\evaluate_repeated.py
- .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v

The random seeds and experiment parameters are defined
directly in the scripts.

## 8. Limitations

1. All financial observations are synthetic.
2. Only four stochastic regimes are repeatedly evaluated.
3. The fixed six-month window has not been optimized.
4. Rolling-origin errors within a series are dependent.
5. No confidence intervals or significance claims are made.
6. Results do not establish real-world forecast accuracy.
7. The evaluation covers one-step cash-flow forecasts, not
   long-horizon company survival or actual insolvency.
8. Seasonality, inflation, financing and debt obligations
   are not explicitly modeled.
9. Scenario assumptions are not calibrated probabilities.

## 9. Conclusion

The trailing mean is a transparent and reproducible
cash-flow forecasting baseline.

It performs better on some stable or oscillating synthetic
series but worse during trends and structural breaks.

A financial forecasting method should be evaluated against
simple alternatives rather than assumed to be superior.

This project is an analytical demonstration, not
financial advice.
