"""Leakage-aware demand forecasting with chronological, rolling one-day evaluation."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

FEATURES = ["sku_code", "weekday", "month", "sin_year", "cos_year", "weekend",
            "temperature_c", "precip_mm", "promotion", "lag_1", "lag_7", "mean_7"]


@dataclass
class ForecastResult:
    model: RandomForestRegressor
    metrics: pd.DataFrame
    forecasts: pd.DataFrame
    feature_importance: pd.DataFrame
    history: pd.DataFrame


def validate_history(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "sku", "units_sold", "temperature_c", "precip_mm", "promotion"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], errors="raise").dt.normalize()
    for column in ("units_sold", "temperature_c", "precip_mm", "promotion"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if data[list(required)].isna().any().any():
        raise ValueError("Missing history values are not allowed")
    if (data["units_sold"] < 0).any() or (data["precip_mm"] < 0).any():
        raise ValueError("Demand and rainfall must be non-negative")
    if (data["units_sold"] % 1 != 0).any() or (~data["promotion"].isin([0, 1])).any():
        raise ValueError("Demand must be integer units; promotion must be 0 or 1")
    if data.duplicated(["sku", "date"]).any():
        raise ValueError("Duplicate SKU/date rows are not allowed")
    if not (data.groupby("sku").size() >= 80).all():
        raise ValueError("Every SKU needs at least 80 days of history")
    if data.groupby("sku").date.max().nunique() != 1:
        raise ValueError("Every SKU must have the same latest date")
    for sku, group in data.groupby("sku"):
        dates = group.sort_values("date")["date"]
        if not (dates.diff().dropna() == pd.Timedelta(days=1)).all():
            raise ValueError(f"History has missing dates for {sku}")
    return data.sort_values(["sku", "date"]).reset_index(drop=True)


def _date_features(date: pd.Timestamp) -> dict:
    phase = date.dayofyear * 2 * math.pi / 365.25
    return {"weekday": date.weekday(), "month": date.month, "sin_year": math.sin(phase),
            "cos_year": math.cos(phase), "weekend": int(date.weekday() >= 5)}


def _make_frame(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    data = data.copy()
    sku_map = {name: idx for idx, name in enumerate(sorted(data.sku.unique()))}
    data["sku_code"] = data.sku.map(sku_map)
    data["weekday"] = data.date.dt.weekday
    data["month"] = data.date.dt.month
    data["sin_year"] = np.sin(2 * np.pi * data.date.dt.dayofyear / 365.25)
    data["cos_year"] = np.cos(2 * np.pi * data.date.dt.dayofyear / 365.25)
    data["weekend"] = (data.weekday >= 5).astype(int)
    bysku = data.groupby("sku")["units_sold"]
    data["lag_1"] = bysku.shift(1)
    data["lag_7"] = bysku.shift(7)
    data["mean_7"] = data.groupby("sku")["units_sold"].transform(
        lambda x: x.shift(1).rolling(7).mean()
    )
    return data.dropna(subset=FEATURES).copy(), sku_map


def train_and_forecast(history: pd.DataFrame, horizon: int = 14,
                       temperature_shift: float = 0.0,
                       weather: pd.DataFrame | None = None) -> ForecastResult:
    """Backtest on last 28 calendar days, then forecast autoregressively.

    Backtest is *rolling one-day ahead*: lags in test rows are observed prior-day
    sales, not forecasts. Multi-day future projections compound prediction errors.
    """
    if not 1 <= horizon <= 30:
        raise ValueError("Forecast horizon must be from 1 to 30 days")
    data = validate_history(history)
    frame, sku_map = _make_frame(data)
    end_date = frame.date.max()
    split = end_date - pd.Timedelta(days=27)
    train = frame[frame.date < split]
    test = frame[frame.date >= split]
    if train.empty or test.empty:
        raise ValueError("Not enough history for a chronological holdout")
    model = RandomForestRegressor(n_estimators=75, max_depth=13, min_samples_leaf=2,
                                  random_state=42, n_jobs=-1)
    model.fit(train[FEATURES], train.units_sold)
    predicted = np.maximum(0, model.predict(test[FEATURES]))
    test = test.copy()
    test["predicted"] = predicted
    test["naive"] = test["mean_7"]
    scores = []
    for sku, group in test.groupby("sku"):
        scores.append({"sku": sku, "mae": float(mean_absolute_error(group.units_sold, group.predicted)),
                       "baseline_mae": float(mean_absolute_error(group.units_sold, group.naive)),
                       "validation_days": len(group)})
    forecasts = []
    for sku, group in data.groupby("sku"):
        sorted_group = group.sort_values("date")
        series = sorted_group.units_sold.astype(float).tolist()
        last_weather = sorted_group.iloc[-1]
        for day in range(1, horizon + 1):
            date = end_date + pd.Timedelta(days=day)
            weather_row = weather.loc[weather.date == date] if weather is not None else pd.DataFrame()
            temp = (float(weather_row.iloc[0].temperature_c) if len(weather_row)
                    else float(last_weather.temperature_c)) + temperature_shift
            rain = float(weather_row.iloc[0].precip_mm) if len(weather_row) else float(last_weather.precip_mm)
            feats = {"sku_code": sku_map[sku], **_date_features(date),
                     "temperature_c": temp, "precip_mm": rain, "promotion": 0,
                     "lag_1": series[-1], "lag_7": series[-7],
                     "mean_7": float(np.mean(series[-7:]))}
            x = pd.DataFrame([{name: feats[name] for name in FEATURES}])
            value = max(0.0, float(model.predict(x)[0]))
            forecasts.append({"date": date, "sku": sku, "predicted_units": value,
                              "temperature_c": temp, "source": "model projection"})
            series.append(value)
    importance = pd.DataFrame({"feature": FEATURES,
                               "importance": model.feature_importances_}).sort_values(
                                   "importance", ascending=False)
    return ForecastResult(model=model, metrics=pd.DataFrame(scores),
                          forecasts=pd.DataFrame(forecasts),
                          feature_importance=importance, history=test)
