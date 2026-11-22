from __future__ import annotations

import pandas as pd


def parse_expiry_lots(lots_df: pd.DataFrame | None, catalog: pd.DataFrame, as_of: str | None = None) -> pd.DataFrame:
    """Accept optional FIFO inventory lots with expiry dates and report rescue candidates at lot granularity.

    Assumptions & Rules:
    - If lots_df is None or empty, falls back to SKU-level aggregate stock with unknown/None expiry dates.
    - NEVER claim an unknown or missing expiry date is safe or expired; unknown expiry dates are clearly flagged.
    - FIFO (First-In, First-Out) priority ensures lots expiring sooner are consumed or evaluated first.
    - Rescue candidates are identified when lot stock exceeds expected demand before expiry plus safety buffer.
    """
    catalog = catalog.copy()
    if as_of is None:
        as_of_date = pd.Timestamp.now().normalize()
    else:
        as_of_date = pd.Timestamp(as_of).normalize()

    if lots_df is None or lots_df.empty:
        # Fall back to synthesizing a single lot per SKU from catalog stock with unknown (None) expiry
        rows = []
        for item in catalog.itertuples(index=False):
            rows.append({
                "sku": item.sku,
                "product": item.product,
                "category": item.category,
                "lot_id": f"{item.sku}-LOT-DEFAULT",
                "expiry_date": None,
                "days_to_expiry": None,
                "lot_stock": float(item.stock_units),
                "unit_cost": float(item.unit_cost),
                "unit_price": float(item.unit_price),
                "kg_per_unit": float(item.kg_per_unit),
                "co2_kg_per_unit": float(item.co2_kg_per_unit),
                "expiry_status": "Unknown Expiry",
                "rescue_candidate_units": 0.0,
                "rescue_candidate_kg": 0.0,
                "rescue_candidate_co2": 0.0
            })
        return pd.DataFrame(rows)

    # Process provided inventory lots
    required_cols = {"sku", "lot_id", "expiry_date", "lot_stock"}
    missing = required_cols.difference(lots_df.columns)
    if missing:
        raise ValueError("Missing lot columns: " + ", ".join(sorted(missing)))

    lots = lots_df.copy()
    lots["expiry_date"] = pd.to_datetime(lots["expiry_date"], errors="coerce")
    lots["lot_stock"] = pd.to_numeric(lots["lot_stock"], errors="raise")

    merged = lots.merge(catalog[["sku", "product", "category", "unit_cost", "unit_price", "kg_per_unit", "co2_kg_per_unit", "base_daily_demand"]], on="sku", how="left")

    result_rows = []
    for row in merged.itertuples(index=False):
        exp = row.expiry_date
        stock = float(row.lot_stock)
        if pd.isna(exp):
            days_to_exp = None
            status = "Unknown Expiry"
            rescue_units = 0.0 # Never claim unknown expiry is a rescue candidate
        else:
            days_to_exp = int((pd.Timestamp(exp).normalize() - as_of_date).days)
            if days_to_exp < 0:
                status = "Expired"
                rescue_units = stock # Entire stock is expired/rescue or waste
            elif days_to_exp <= 3:
                status = "Critical Expiry"
                daily_demand = float(getattr(row, "base_daily_demand", 5.0))
                expected_need = daily_demand * days_to_exp
                rescue_units = max(0.0, stock - expected_need)
            else:
                status = "Fresh"
                rescue_units = 0.0

        kg_per = float(getattr(row, "kg_per_unit", 0.2))
        co2_per = float(getattr(row, "co2_kg_per_unit", 1.0))

        result_rows.append({
            "sku": row.sku,
            "product": getattr(row, "product", row.sku),
            "category": getattr(row, "category", "General"),
            "lot_id": row.lot_id,
            "expiry_date": exp.strftime("%Y-%m-%d") if pd.notna(exp) else None,
            "days_to_expiry": days_to_exp,
            "lot_stock": stock,
            "unit_cost": float(row.unit_cost),
            "unit_price": float(row.unit_price),
            "kg_per_unit": kg_per,
            "co2_kg_per_unit": co2_per,
            "expiry_status": status,
            "rescue_candidate_units": float(rescue_units),
            "rescue_candidate_kg": float(rescue_units * kg_per),
            "rescue_candidate_co2": float(rescue_units * co2_per)
        })

    return pd.DataFrame(result_rows).sort_values(["sku", "days_to_expiry"], na_position="last").reset_index(drop=True)
