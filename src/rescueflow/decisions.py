"""Deterministic, auditable reorder and food-rescue decision support."""
from __future__ import annotations

import math
import pandas as pd


def make_recommendations(catalog: pd.DataFrame, forecast: pd.DataFrame,
                         budget: float = 1200.0, safety_days: float = 1.5,
                         days: int = 7) -> pd.DataFrame:
    """Rank inventory orders by expected avoided shortage margin per spend.

    Approximation only, not a constrained optimum: no supplier min-order packs,
    storage temperature, expiry lots or delivery-route constraints are modeled.
    """
    if budget < 0 or safety_days < 0 or days < 1:
        raise ValueError("Budget and safety days cannot be negative; days must be >= 1")
    rows = []
    for item in catalog.itertuples(index=False):
        f = forecast[forecast.sku == item.sku].sort_values("date")
        if f.empty:
            raise ValueError(f"No forecast for SKU {item.sku}")
        daily = float(f.predicted_units.mean())
        next_week = float(f.head(days).predicted_units.sum())
        lead_demand = daily * item.lead_days
        target = math.ceil(lead_demand + safety_days * daily)
        desired = max(0, target - int(item.stock_units))
        # Avoid recommending inventory above approximate sales inside shelf life.
        shelf_cap = max(0, math.ceil(daily * item.shelf_life_days) - int(item.stock_units))
        desired = min(desired, shelf_cap)
        gross_margin = max(0.0, float(item.unit_price - item.unit_cost))
        shortage_units = max(0.0, lead_demand - item.stock_units)
        expected_donation = max(0, math.floor(item.stock_units - daily * item.shelf_life_days - safety_days * daily))
        impact = min(desired, shortage_units + daily * safety_days) * gross_margin
        rows.append({"sku": item.sku, "product": item.product, "category": item.category,
                     "on_hand": int(item.stock_units), "daily_prediction": daily,
                     "forecast_7d": next_week, "lead_days": int(item.lead_days),
                     "shelf_life_days": int(item.shelf_life_days),
                     "unit_cost": float(item.unit_cost), "margin": gross_margin,
                     "order_needed": desired, "order_units": 0,
                     "shortage_risk_units": shortage_units,
                     "donation_units": int(expected_donation),
                     "donation_kg": expected_donation * float(item.kg_per_unit),
                     "avoided_co2_kg_proxy": expected_donation * float(item.co2_kg_per_unit),
                     "priority_score": impact / max(0.01, desired * float(item.unit_cost)) if desired else 0})
    frame = pd.DataFrame(rows).sort_values(["priority_score", "shortage_risk_units"],
                                              ascending=[False, False]).reset_index(drop=True)
    remaining = budget
    for index, row in frame.iterrows():
        quantity = min(int(row.order_needed), int((remaining + 1e-9) // row.unit_cost))
        frame.at[index, "order_units"] = quantity
        remaining -= quantity * row.unit_cost
    frame["order_cost"] = frame.order_units * frame.unit_cost
    frame["reason"] = frame.apply(
        lambda x: (f"Projected {x.daily_prediction:.1f}/day; {x.lead_days}-day replenishment lead. "
                   + ("Prioritize replenishment." if x.order_units else
                      "No budgeted order recommended.")
                   + (f" Potential donation: {x.donation_units} units." if x.donation_units else "")),
        axis=1)
    return frame
