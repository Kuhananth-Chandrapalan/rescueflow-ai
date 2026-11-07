"""Stockout risk scoring and proxy probability estimation based on lead time and demand."""
from __future__ import annotations

import math
import pandas as pd


def calculate_stockout_risk(catalog: pd.DataFrame, forecast: pd.DataFrame, horizon: int = 7) -> pd.DataFrame:
    """Calculate a calibrated proxy stockout risk score per SKU based on inventory, lead time, and forecast.

    Assumptions & Limitations:
    - Stockout probability is modeled as a heuristic logistic/sigmoid function of the ratio between lead-time demand and available stock, adjusted by daily demand variance.
    - Does not account for emergency replenishment, multi-echelon stock, or instantaneous supplier deliveries.
    - Designed as a relative triage score, not an exact actuarial failure probability.
    """
    rows = []
    for item in catalog.itertuples(index=False):
        f = forecast[forecast.sku == item.sku].sort_values("date")
        if f.empty:
            raise ValueError(f"No forecast available for SKU {item.sku}")

        daily_mean = float(f.predicted_units.mean())
        lead_days = float(item.lead_days)
        stock = float(item.stock_units)

        # Expected demand during the supplier lead time
        lead_time_demand = daily_mean * lead_days

        # Shortage gap relative to stock
        shortage_gap = lead_time_demand - stock

        # Proxy risk score (sigmoid-calibrated risk probability between 0 and 1)
        scale = max(0.1, lead_time_demand * 0.5)
        arg = -shortage_gap / scale
        if arg > 100.0:
            risk_prob = 0.0
        elif arg < -100.0:
            risk_prob = 1.0
        else:
            risk_prob = 1.0 / (1.0 + math.exp(arg))

        if risk_prob >= 0.75:
            badge = "🚨 High Risk"
        elif risk_prob >= 0.40:
            badge = "⚠️ Moderate Risk"
        else:
            badge = "✅ Secure"

        rows.append({
            "sku": item.sku,
            "product": item.product,
            "category": item.category,
            "stock_units": stock,
            "lead_days": lead_days,
            "daily_demand": daily_mean,
            "lead_time_demand": lead_time_demand,
            "stockout_probability": float(risk_prob),
            "risk_badge": badge
        })

    return pd.DataFrame(rows)
