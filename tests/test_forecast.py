import pandas as pd
import pytest

from rescueflow.demo import demo_history
from rescueflow.forecast import train_and_forecast, validate_history


def test_validation_rejects_duplicates():
    history = demo_history(days=90)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_history(pd.concat([history, history.iloc[:1]], ignore_index=True))


def test_validation_rejects_gaps():
    history = demo_history(days=90)
    one = history.sku.iloc[0]
    history = history.loc[~((history.sku == one) & (history.date == sorted(history.date.unique())[40]))]
    with pytest.raises(ValueError):
        validate_history(history)


def test_forecasts_are_nonnegative_and_have_future_dates():
    data = demo_history(days=110)
    result = train_and_forecast(data, horizon=7)
    assert len(result.forecasts) == data.sku.nunique() * 7
    assert result.forecasts.predicted_units.ge(0).all()
    assert result.forecasts.date.min() > data.date.max()
    assert result.metrics.validation_days.eq(28).all()
    assert result.metrics.mae.ge(0).all()
    assert result.metrics.baseline_mae.ge(0).all()


def test_prediction_intervals_present_and_ordered():
    data = demo_history(days=110)
    result = train_and_forecast(data, horizon=7)
    f = result.forecasts
    assert "lower_units" in f.columns
    assert "upper_units" in f.columns
    assert f.lower_units.le(f.predicted_units).all()
    assert f.upper_units.ge(f.predicted_units).all()
    assert f.lower_units.ge(0).all()


def test_horizon_guard():
    with pytest.raises(ValueError):
        train_and_forecast(demo_history(days=110), horizon=40)
