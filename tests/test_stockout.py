import pandas as pd
import pytest
from rescueflow.demo import inventory_catalog
from rescueflow.stockout import calculate_stockout_risk


def sample_forecast(amount: float = 5.0) -> pd.DataFrame:
    catalog = inventory_catalog()
    return pd.DataFrame([{
        'sku': sku,
        'date': pd.Timestamp('2026-11-06') + pd.Timedelta(days=d),
        'predicted_units': amount
    } for sku in catalog.sku for d in range(7)])


def test_stockout_risk_normal_case():
    catalog = inventory_catalog()
    forecast = sample_forecast(10.0)
    result = calculate_stockout_risk(catalog, forecast)
    assert 'stockout_probability' in result.columns
    assert 'risk_badge' in result.columns
    assert result.stockout_probability.between(0.0, 1.0).all()
    assert len(result) == len(catalog)


def test_stockout_risk_zero_stock_edge_case():
    catalog = inventory_catalog().copy()
    catalog['stock_units'] = 0.0
    forecast = sample_forecast(15.0)
    result = calculate_stockout_risk(catalog, forecast)
    # With zero stock and high demand, probability should be very high
    assert (result.stockout_probability > 0.8).all()
    assert (result.risk_badge == '🚨 High Risk').all()


def test_stockout_risk_abundant_stock_edge_case():
    catalog = inventory_catalog().copy()
    catalog['stock_units'] = 10000.0
    forecast = sample_forecast(2.0)
    result = calculate_stockout_risk(catalog, forecast)
    assert (result.stockout_probability < 0.05).all()
    assert (result.risk_badge == '✅ Secure').all()


def test_stockout_missing_forecast_raises():
    catalog = inventory_catalog()
    empty_forecast = pd.DataFrame(columns=['sku', 'date', 'predicted_units'])
    with pytest.raises(ValueError):
        calculate_stockout_risk(catalog, empty_forecast)
