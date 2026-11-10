from __future__ import annotations

import pandas as pd


DEFAULT_REGIONAL_HOLIDAYS = {
    "2026-04-13": "Sinhala & Tamil New Year Eve",
    "2026-04-14": "Sinhala & Tamil New Year",
    "2026-05-01": "May Day",
    "2026-12-25": "Christmas Day",
    "2026-12-31": "New Year\'s Eve",
}


def apply_holiday_and_promotion_scenario(
    history: pd.DataFrame,
    holiday_dates: list[str] | dict[str, str] | None = None,
    extra_promotions: list[str] | None = None,
    demand_multiplier: float = 1.35,
) -> pd.DataFrame:
    """Apply controlled regional holiday and promotion demand scenarios to historical or forecast data.

    Assumptions & Limitations:
    - Holiday demand surges are modeled via deterministic multipliers based on regional retail patterns.
    - These are scenario projections, not verified econometric models; actual behavior varies.
    - Promotion flags are binary (0/1) indicators affecting baseline and holiday uplift interactions.
    """
    data = history.copy()
    data["date"] = pd.to_datetime(data["date"])

    if holiday_dates is None:
        holiday_dates = DEFAULT_REGIONAL_HOLIDAYS

    if isinstance(holiday_dates, list):
        h_set = set(pd.to_datetime(holiday_dates))
    else:
        h_set = set(pd.to_datetime(list(holiday_dates.keys())))

    if "holiday" not in data.columns:
        data["holiday"] = 0
    if "promotion" not in data.columns:
        data["promotion"] = 0

    mask_holiday = data["date"].isin(h_set)
    data.loc[mask_holiday, "holiday"] = 1
    data.loc[mask_holiday, "units_sold"] = (
        data.loc[mask_holiday, "units_sold"] * demand_multiplier
    ).round().astype(int)

    if extra_promotions:
        promo_dates = set(pd.to_datetime(extra_promotions))
        mask_promo = data["date"].isin(promo_dates)
        data.loc[mask_promo, "promotion"] = 1
        data.loc[mask_promo, "units_sold"] = (
            data.loc[mask_promo, "units_sold"] * 1.25
        ).round().astype(int)

    return data.sort_values(["sku", "date"]).reset_index(drop=True)
