import pandas as pd
import pytest
from rescueflow.demo import demo_history
from rescueflow.holiday import apply_holiday_and_promotion_scenario


def test_holiday_scenario_applies_uplift():
    history = demo_history(days=90, as_of="2026-05-10")
    target_date = "2026-05-01"
    original = history[history.date == target_date].copy()
    modified = apply_holiday_and_promotion_scenario(history, holiday_dates=[target_date], demand_multiplier=2.0)
    mod_subset = modified[modified.date == target_date]
    assert (mod_subset.holiday == 1).all()
    assert (mod_subset.units_sold >= original.units_sold).all()


def test_extra_promotion_scenario():
    history = demo_history(days=90, as_of="2026-05-10")
    promo_date = "2026-05-05"
    modified = apply_holiday_and_promotion_scenario(history, extra_promotions=[promo_date])
    sub = modified[modified.date == promo_date]
    assert (sub.promotion == 1).all()


def test_edge_case_empty_holidays():
    history = demo_history(days=90, as_of="2026-05-10")
    modified = apply_holiday_and_promotion_scenario(history, holiday_dates=[])
    assert "holiday" in modified.columns
    assert modified.holiday.sum() == 0
