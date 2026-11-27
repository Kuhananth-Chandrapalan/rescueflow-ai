from __future__ import annotations

import numpy as np
import pandas as pd


def detect_demand_anomalies(history: pd.DataFrame, window: int = 14, z_threshold: float = 2.5) -> pd.DataFrame:
    """Detect demand anomalies using historical moving statistics per SKU.

    Flags spikes and drops based on rolling z-scores of units_sold relative to past window.
    Provides interpretable flags, severity badges, and false-positive guidance.
    """
    required = {"date", "sku", "units_sold"}
    if not required.issubset(history.columns):
        raise ValueError("History missing required columns for anomaly detection")

    data = history.sort_values(["sku", "date"]).copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")

    # Calculate rolling mean and standard deviation per SKU
    grouped = data.groupby("sku")["units_sold"]
    rolling_mean = grouped.transform(lambda x: x.shift(1).rolling(window=window, min_periods=7).mean())
    rolling_std = grouped.transform(lambda x: x.shift(1).rolling(window=window, min_periods=7).std())

    # Fallback for initial rows or zero variance
    rolling_std = rolling_std.fillna(0.0).replace(0.0, 1.0)
    rolling_mean = rolling_mean.fillna(grouped.transform("mean"))

    data["expected_demand"] = rolling_mean
    data["residual"] = data["units_sold"] - data["expected_demand"]
    data["z_score"] = (data["units_sold"] - data["expected_demand"]) / rolling_std

    def classify_anomaly(row):
        z = row["z_score"]
        if pd.isna(z):
            return "Normal", "ℹ️ Insufficient History"
        if z >= z_threshold:
            return "High Spike", "🚨 Potential Demand Surge (Check promotions, holidays, or data error)"
        elif z <= -z_threshold:
            return "Sharp Drop", "⚠️ Potential Demand Drop (Check stockouts, recording gaps, or weather)"
        elif z >= (z_threshold * 0.7):
            return "Moderate Spike", "⚠️ Elevated Demand"
        elif z <= -(z_threshold * 0.7):
            return "Moderate Drop", "⚡ Reduced Demand"
        else:
            return "Normal", "✅ Normal"

    classifications = data.apply(classify_anomaly, axis=1)
    data["anomaly_type"] = [c[0] for c in classifications]
    data["anomaly_flag"] = [c[1] for c in classifications]
    data["is_anomaly"] = data["anomaly_type"].isin(["High Spike", "Sharp Drop"])

    return data.sort_values(["date", "sku"]).reset_index(drop=True)
