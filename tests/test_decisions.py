import pandas as pd
import pytest
from rescueflow.demo import inventory_catalog
from rescueflow.decisions import make_recommendations
from rescueflow.report import impact_summary


def forecasts(amount: float = 5.0) -> pd.DataFrame:
    catalog = inventory_catalog()
    return pd.DataFrame([{'sku': sku, 'date': pd.Timestamp('2026-11-06') + pd.Timedelta(days=d),
                          'predicted_units': amount} for sku in catalog.sku for d in range(7)])


def test_budget_never_exceeded():
    catalog = inventory_catalog().copy()
    catalog['stock_units'] = 0
    frame = make_recommendations(catalog, forecasts(10), budget=60)
    assert frame.order_cost.sum() <= 60.000001
    assert frame.order_units.le(frame.order_needed + frame.pack_size).all()
    assert frame.order_units.ge(0).all()


def test_zero_budget_gives_no_orders():
    catalog = inventory_catalog().copy()
    catalog['stock_units'] = 0
    result = make_recommendations(catalog, forecasts(8), budget=0)
    assert result.order_units.sum() == 0
    assert result.order_cost.sum() == 0


def test_excess_stock_creates_rescue_candidates():
    catalog = inventory_catalog().copy()
    catalog.loc[catalog.sku == 'BAN-01', 'stock_units'] = 900
    decisions = make_recommendations(catalog, forecasts(4), budget=100)
    banana = decisions.loc[decisions.sku == 'BAN-01'].iloc[0]
    assert banana.donation_units > 0
    assert banana.donation_kg > 0
    assert banana.order_units == 0


def test_summary_is_coherent():
    result = make_recommendations(inventory_catalog(), forecasts(), budget=100)
    summary = impact_summary(result, 100)
    assert summary['budget_remaining'] >= 0
    assert summary['order_units'] == result.order_units.sum()


def test_invalid_budget_rejected():
    with pytest.raises(ValueError):
        make_recommendations(inventory_catalog(), forecasts(), budget=-5)


def test_pack_sizing_and_moq():
    catalog = inventory_catalog().copy()
    # Set specific pack size and MOQ for testing
    catalog.loc[catalog.sku == 'BAN-01', 'stock_units'] = 0
    catalog.loc[catalog.sku == 'BAN-01', 'pack_size'] = 12
    catalog.loc[catalog.sku == 'BAN-01', 'min_order_qty'] = 24
    forecast = forecasts(5.0)
    decisions = make_recommendations(catalog, forecast, budget=500.0)
    banana = decisions.loc[decisions.sku == 'BAN-01'].iloc[0]
    # Order units must be a multiple of pack_size (12)
    assert banana.order_units % 12 == 0
    # Order units must meet MOQ if ordered
    if banana.order_units > 0:
        assert banana.order_units >= 24
