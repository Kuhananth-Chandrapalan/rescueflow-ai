# Multi-Horizon Backtesting & Model Quality

## Assumptions & Methodology
RescueFlow AI implements true multi-horizon rolling backtesting (7-day and 14-day horizons) alongside rolling one-day-ahead out-of-sample evaluation.

1. **No Target Leakage:** At historical cutoffs, multi-day rollouts are computed autoregressively. Lag features for subsequent steps are populated using prior model predictions rather than ground truth.
2. **Error Accumulation:** As the planning horizon expands from 1 day to 7 or 14 days, forecast error typically increases due to compounding prediction errors in lag features.
3. **Baseline Comparison:** Model MAE is benchmarked against a 7-day rolling historical mean baseline.

## Model and Data Limits
- Synthetic demonstration data exhibits stationary patterns that may not reflect real-world seasonal shocks, supply disruptions, or sudden demand spikes.
- Prediction intervals rely on empirical residual quantiles scaled by square root time, assuming stationary residual distributions.

## User-Facing Interpretation
- **Rolling 1-day MAE**: Reflects immediate day-ahead precision.
- **7/14-day Horizon MAE**: Reflects long-range cumulative forecasting accuracy. Operators should expect higher error rates at 14 days, requiring appropriate safety stock buffers.
