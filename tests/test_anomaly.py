import pandas as pd
import pytest
from rescueflow.demo import demo_history
from rescueflow.anomaly import detect_demand_anomalies


def test_detect_demand_anomalies_normal():
    history = demo_history(days=90)
    res = detect_demand_anomalies(history)
    assert "anomaly_type" in res.columns
    assert "z_score" in res.columns
    assert "is_anomaly" in res.columns
    assert len(res) == len(history)


def test_detect_demand_anomalies_spike_edge_case():
    history = demo_history(days=90)
    # Artificially inject a massive spike for one SKU on the last day
    last_date = history.date.max()
    sku = history.sku.iloc[0]
    history.loc[(history.date == last_date) & (history.sku == sku), "units_sold"] = 9999

    res = detect_demand_anomalies(history)
    row = res[(res.date == last_date) & (res.sku == sku)].iloc[0]
    assert row.is_anomaly == True
    assert row.anomaly_type == "High Spike"
    assert "Surge" in row.anomaly_flag


def test_anomaly_missing_columns_raises():
    bad_history = pd.DataFrame([{"date": "2026-11-05", "units_sold": 10}])
    with pytest.raises(ValueError, match="History missing required columns"):
        detect_demand_anomalies(bad_history)
