"""Reproducible *synthetic* grocery data for a privacy-safe demonstration."""
from __future__ import annotations

import numpy as np
import pandas as pd


CATALOG = [
    ("BAN-01", "Bananas", "Produce", 4, 0.42, 0.82, 2, 290, 1.1, 0.16, 38),
    ("TOM-02", "Tomatoes", "Produce", 6, 0.55, 1.15, 2, 58, 0.8, 0.20, 27),
    ("BREAD-03", "Wholemeal bread", "Bakery", 4, 1.10, 2.10, 1, 160, 1.4, 0.5, 25),
    ("MILK-04", "Fresh milk", "Dairy", 7, 0.90, 1.65, 2, 57, 1.8, 1.0, 31),
    ("EGG-05", "Egg cartons", "Dairy", 19, 1.45, 2.55, 3, 48, 1.2, 0.7, 18),
    ("LETT-06", "Lettuce", "Produce", 5, 0.70, 1.40, 2, 47, 0.6, 0.28, 23),
    ("RICE-07", "Rice packs", "Pantry", 180, 1.25, 2.15, 5, 105, 1.7, 1.0, 13),
    ("CHICK-08", "Chilled chicken", "Meat", 5, 3.05, 5.45, 2, 32, 5.5, 0.75, 15),
    ("YOG-09", "Yogurt cups", "Dairy", 11, 0.35, 0.82, 2, 76, 1.4, 0.15, 33),
    ("MANGO-10", "Mangoes", "Produce", 6, 0.95, 1.90, 3, 41, 1.0, 0.32, 20),
]


def inventory_catalog() -> pd.DataFrame:
    columns = ["sku", "product", "category", "shelf_life_days", "unit_cost",
               "unit_price", "lead_days", "stock_units", "co2_kg_per_unit",
               "kg_per_unit", "base_daily_demand"]
    return pd.DataFrame(CATALOG, columns=columns)


def demo_history(days: int = 240, seed: int = 47, as_of: str = "2026-11-05") -> pd.DataFrame:
    """Create demand with trend, weekly cycles, promotions, and temperature signal.

    Values are entirely synthetic and must not be treated as operational evidence.
    Fixed end date ensures repeatable tests and demo screenshots.
    """
    if days < 80:
        raise ValueError("At least 80 days are required for training and backtesting")
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp(as_of), periods=days, freq="D")
    rows: list[dict] = []
    for i, item in inventory_catalog().iterrows():
        for day_index, day in enumerate(dates):
            weekday = day.weekday()
            t = day.dayofyear
            temperature = 28.0 + 2.3 * np.sin(2 * np.pi * t / 365) + rng.normal(0, 1.6)
            rainfall = max(0.0, rng.gamma(1.3, 5.2) - 3.5)
            promo = int(rng.uniform() < 0.055)
            weekly = 1.19 if weekday in (5, 6) else (0.94 if weekday == 1 else 1.0)
            seasonal = 1 + 0.11 * np.sin(2 * np.pi * (t + i * 19) / 365)
            weather_effect = 1 + (temperature - 28) * (0.018 if item.category in ("Produce", "Dairy") else 0.004)
            amount = item.base_daily_demand * weekly * seasonal * weather_effect
            amount *= 1.20 if promo else 1.0
            amount *= 1 + day_index * 0.00022
            demand = max(0, int(round(rng.normal(amount, max(2, amount * 0.13)))))
            rows.append({"date": day, "sku": item.sku, "units_sold": demand,
                         "temperature_c": round(float(temperature), 2),
                         "precip_mm": round(float(rainfall), 2), "promotion": promo})
    return pd.DataFrame(rows).sort_values(["sku", "date"]).reset_index(drop=True)
