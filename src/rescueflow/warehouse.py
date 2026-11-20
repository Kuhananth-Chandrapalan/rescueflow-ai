from __future__ import annotations

import pandas as pd

def add_warehouse_stock(catalog: pd.DataFrame, warehouses: list[str] | None = None) -> pd.DataFrame:
    """Expand catalog inventory across multiple warehouses, preserving single-warehouse fallback."""
    if warehouses is None:
        warehouses = ["Central Warehouse", "North Hub", "South Hub"]
    if "warehouse" in catalog.columns:
        return catalog.copy()
    rows = []
    # Factor stock distribution across warehouses for simulation
    factors = [0.5, 0.3, 0.2]
    for w_idx, warehouse in enumerate(warehouses):
        factor = factors[w_idx % len(factors)]
        for item in catalog.itertuples(index=False):
            d = item._asdict()
            # Distribute stock units proportionally and round
            d["warehouse"] = warehouse
            d["stock_units"] = max(0, int(round(item.stock_units * factor)))
            rows.append(d)
    return pd.DataFrame(rows)


def filter_warehouse_catalog(catalog: pd.DataFrame, warehouse: str | None) -> pd.DataFrame:
    """Filter catalog by specific warehouse or return aggregate/fallback if not applicable."""
    if "warehouse" not in catalog.columns or warehouse is None or warehouse == "All Warehouses":
        if "warehouse" in catalog.columns:
            # Aggregate back across warehouses if All is selected
            agg_cols = {
                "product": "first",
                "category": "first",
                "shelf_life_days": "first",
                "unit_cost": "first",
                "unit_price": "first",
                "lead_days": "first",
                "stock_units": "sum",
                "co2_kg_per_unit": "first",
                "kg_per_unit": "first",
                "base_daily_demand": "first",
                "pack_size": "first",
                "min_order_qty": "first"
            }
            return catalog.groupby("sku", as_index=False).agg(agg_cols)
        return catalog.copy()
    filtered = catalog[catalog.warehouse == warehouse].copy()
    return filtered
