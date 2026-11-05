"""Optional no-key weather forecast for a non-commercial demo."""
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen
import pandas as pd


def get_weather(latitude: float = 6.9271, longitude: float = 79.8612,
                days: int = 14, timeout: int = 10) -> pd.DataFrame:
    """Download daily temperature/rainfall forecasts from Open-Meteo.

    Must be explicitly requested by the UI. Caller can fall back to demo weather.
    """
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid geographic coordinates")
    if not 1 <= days <= 16:
        raise ValueError("Open-Meteo forecast days must be between 1 and 16")
    query = urlencode({"latitude": latitude, "longitude": longitude,
                       "daily": "temperature_2m_mean,precipitation_sum",
                       "forecast_days": days, "timezone": "Asia/Colombo"})
    with urlopen("https://api.open-meteo.com/v1/forecast?" + query, timeout=timeout) as stream:
        payload = json.load(stream)
    daily = payload["daily"]
    return pd.DataFrame({"date": pd.to_datetime(daily["time"]),
                         "temperature_c": daily["temperature_2m_mean"],
                         "precip_mm": daily["precipitation_sum"]})
