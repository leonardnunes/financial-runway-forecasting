# Financial Runway Forecasting — Methodology

## 1. Objective

Estimate future cash balances and financial runway from historical
monthly revenue and expense observations.

This project provides transparent deterministic projections,
scenario analysis, and retrospective evaluation.

It does not provide probabilistic forecasts or financial advice.

## 2. Input data

Each observation contains:

- Period in YYYY-MM format.
- Monthly revenue.
- Monthly expenses.

Records must be chronologically ordered, unique, and consecutive.
At least three observations are required.

All monetary values must be finite Decimal values or decimal strings.
Binary floating-point inputs are rejected to avoid implicit rounding.
Historical revenue and expenses must be nonnegative.

The starting cash balance represents available cash at the end of
the final observed month. It must be finite and nonnegative.

All values must use the same currency. Currency conversion is outside
the scope of this project.

## 3. Estimation method

Use a trailing historical window of w months.

The default window is min(6, N), where N is the available number
of monthly observations. A custom window must satisfy 3 <= w <= N.

Expected monthly revenue:

R_hat = sum(revenue over last w months) / w

Expected monthly expenses:

D_hat = sum(expenses over last w months) / w

The initial model is a trailing-mean baseline. It does not extrapolate
trends, seasonality, inflation, or structural breaks.

## 4. Scenario analysis

Each scenario defines two nonnegative multipliers:

- alpha: revenue multiplier.
- beta: expense multiplier.

Projected monthly net cash flow:

F = alpha * R_hat - beta * D_hat

Default illustrative scenarios:

- Base: alpha = 1.00, beta = 1.00.
- Downside: alpha = 0.90, beta = 1.10.
- Upside: alpha = 1.10, beta = 0.95.

Scenario assumptions are not empirical probabilities.

## 5. Cash balance projection

For a constant monthly scenario cash flow F:

C_t = C_0 + t * F

The first forecast period is the month after the last historical
observation. The default forecast horizon is 12 months.

Forecasts may show negative hypothetical balances for diagnostic
purposes. This does not imply access to credit or external funding.

## 6. Burn rate and runway

Net monthly burn:

B = max(-F, 0)

If C_0 = 0, runway is 0 months because cash is already exhausted.

If C_0 > 0 and B > 0:

runway_months = C_0 / B

If C_0 > 0 and B = 0, runway is undefined under the constant-flow
assumptions because the projected cash balance does not decrease.

Fractional months assume cash flow occurs uniformly within each
month. A runway beyond the display horizon remains an estimate,
not a verified survival period.

## 7. Input validation and precision

Reject malformed dates, duplicate or missing months, negative
historical revenue or expenses, unsupported monetary types,
nonfinite values, and invalid scenario multipliers.

Use decimal arithmetic for monetary calculations. Avoid introducing
binary floating-point values through intermediate operations.

Avoid cumulative rounding during projection. Formatting to two
decimal places is a presentation concern.

## 8. Retrospective evaluation

Use rolling-origin, one-step-ahead evaluation.

At each eligible historical origin:

1. Use only observations available at that origin.
2. Estimate next-month revenue and expenses from the trailing window.
3. Predict next-month net cash flow.
4. Compare the prediction with realized net cash flow.

Report mean absolute error (MAE) and mean error (bias).
Compare against a naive baseline that predicts the previous
month's net cash flow.

Do not use future observations to select parameters at an earlier
forecast origin.

At least one observation beyond the chosen training window is
needed to calculate retrospective forecast errors.

This evaluation measures one-step cash-flow accuracy. It does not
directly validate long-horizon survival estimates.

## 9. Limitations

- Constant monthly cash-flow assumptions.
- Sensitivity to historical outliers.
- No explicit seasonality or trend model.
- No customer-level forecasts.
- No debt covenants, financing events, or credit facilities.
- No prediction intervals or calibrated scenario probabilities.
- Synthetic demonstration data cannot establish real-world accuracy.

Results are analytical estimates, not guaranteed financial outcomes.
