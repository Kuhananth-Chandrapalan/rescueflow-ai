"""Quality checks for uploaded source data."""
from __future__ import annotations

import pandas as pd
from .forecast import validate_history

REQUIRED_CATALOG = {"sku", "product", "category", "shelf_life_days", "unit_cost", "unit_price",
                    "lead_days", "stock_units", "co2_kg_per_unit", "kg_per_unit"}


def validate_catalog(items: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_CATALOG.difference(items.columns)
    if missing:
        raise ValueError("Missing inventory columns: " + ", ".join(sorted(missing)))
    catalog = items.copy()
    if catalog.sku.isna().any() or catalog.sku.duplicated().any():
        raise ValueError("SKU identifiers must be present and unique")
    numerical = ["shelf_life_days", "unit_cost", "unit_price", "lead_days",
                 "stock_units", "co2_kg_per_unit", "kg_per_unit"]
    for col in numerical:
        catalog[col] = pd.to_numeric(catalog[col], errors="raise")
    if catalog[numerical].isna().any().any() or (catalog[numerical] < 0).any().any():
        raise ValueError("Inventory numerical values must be nonnegative and nonmissing")
    if (catalog.shelf_life_days < 1).any() or (catalog.unit_cost <= 0).any():
        raise ValueError("Shelf life and unit cost must be positive")
    return catalog


def validate_pair(history: pd.DataFrame, inventory: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h, c = validate_history(history), validate_catalog(inventory)
    if set(h.sku) != set(c.sku):
        raise ValueError("Historical and inventory SKUs must match exactly")
    return h, c
