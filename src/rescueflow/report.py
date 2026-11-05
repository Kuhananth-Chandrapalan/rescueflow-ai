"""Compact summaries for dashboard and CSV exports."""
from __future__ import annotations

import pandas as pd


def impact_summary(recommendations: pd.DataFrame, budget: float) -> dict:
    return {
        "total_forecast_units": round(float(recommendations.forecast_7d.sum())),
        "order_units": int(recommendations.order_units.sum()),
        "order_spend": round(float(recommendations.order_cost.sum()), 2),
        "budget_remaining": round(float(budget - recommendations.order_cost.sum()), 2),
        "donation_kg": round(float(recommendations.donation_kg.sum()), 1),
        "high_risk_products": int((recommendations.shortage_risk_units > 0).sum()),
        "proxy_co2_kg": round(float(recommendations.avoided_co2_kg_proxy.sum()), 1),
    }
