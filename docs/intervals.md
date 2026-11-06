# Calibrated Prediction Intervals & Assumptions

RescueFlow AI implements empirical quantile bands to quantify demand uncertainty over multi-day planning horizons.

## Methodology

1. **Validation Residuals**: During the rolling chronological backtest (last 28 days of history), the model generates point predictions and computes residual errors ($e_t = y_t - \hat{y}_t$) for each SKU.
2. **Empirical Quantiles**: The 10th and 90th percentiles of the holdout residuals are computed per SKU, establishing an empirical 80% coverage band.
3. **Horizon Scaling**: Because uncertainty compounds over multi-step autoregressive forecasts, interval widths scale proportionally with $\sqrt{\text{horizon day}}$.

## Assumptions and Limits

- **Stationarity**: The method assumes future demand error distributions resemble the recent 28-day validation period.
- **External Validation Requirement**: Coverage guarantees and nominal quantile levels are empirical approximations derived from synthetic or historical test splits. Real-world validation against live operating data is strictly required prior to deploying intervals for inventory buffer sizing.
