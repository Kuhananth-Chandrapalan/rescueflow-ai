"""Deterministic, auditable reorder and food-rescue decision support."""
from __future__ import annotations

import math
import pandas as pd


def make_recommendations(catalog: pd.DataFrame, forecast: pd.DataFrame,
                         budget: float = 1200.0, safety_days: float = 1.5,
                         days: int = 7) -> pd.DataFrame:
    """Rank inventory orders by expected avoided shortage margin per spend.

    Supports supplier pack sizes (integer multiples) and minimum order quantities
    under a hard budget cap.
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
        shelf_cap = max(0, math.ceil(daily * item.shelf_life_days) - int(item.stock_units))
        desired = min(desired, shelf_cap)

        pack_size = max(1, int(getattr(item, "pack_size", 1)))
        moq = int(getattr(item, "min_order_qty", 0))

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
                     "pack_size": pack_size, "min_order_qty": moq,
                     "shortage_risk_units": shortage_units,
                     "donation_units": int(expected_donation),
                     "donation_kg": expected_donation * float(item.kg_per_unit),
                     "avoided_co2_kg_proxy": expected_donation * float(item.co2_kg_per_unit),
                     "priority_score": impact / max(0.01, desired * float(item.unit_cost)) if desired else 0})

    frame = pd.DataFrame(rows).sort_values(["priority_score", "shortage_risk_units"],
                                              ascending=[False, False]).reset_index(drop=True)
    remaining = budget

    # First pass: satisfy minimum order constraints and pack sizes within budget
    for index, row in frame.iterrows():
        raw_needed = int(row.order_needed)
        moq = int(row.min_order_qty)
        pack = int(row.pack_size)

        if raw_needed <= 0:
            order_qty = 0
        else:
            # If we need anything, we must meet at least MOQ if specified
            target_qty = max(raw_needed, moq)
            # Round up to nearest pack multiple
            multiples = math.ceil(target_qty / pack)
            order_qty = multiples * pack

        cost = order_qty * row.unit_cost
        if cost <= remaining + 1e-9:
            frame.at[index, "order_units"] = order_qty
            remaining -= cost
        else:
            # Try smaller pack sizes or exact MOQ if possible, or pack-rounded fit within remaining budget
            possible_packs = int((remaining + 1e-9) // (pack * row.unit_cost))
            feasible_qty = possible_packs * pack
            if feasible_qty >= moq and feasible_qty > 0:
                frame.at[index, "order_units"] = feasible_qty
                remaining -= feasible_qty * row.unit_cost
            else:
                frame.at[index, "order_units"] = 0

    frame["order_cost"] = frame.order_units * frame.unit_cost
    frame["reason"] = frame.apply(
        lambda x: (f"Projected {x.daily_prediction:.1f}/day; {x.lead_days}-day lead. "
                   f"Pack size: {x.pack_size}, MOQ: {x.min_order_qty}. "
                   + ("Prioritize replenishment." if x.order_units else
                      "No budgeted order recommended / budget or MOQ constrained.")
                   + (f" Potential donation: {x.donation_units} units." if x.donation_units else "")),
        axis=1)
    return frame
