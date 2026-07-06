from datetime import date, datetime, timezone

import requests

from config import OPEN_METEO_BASE_URL
from models import HourlyWeather
from weather.base import WeatherProvider


class OpenMeteoProvider(WeatherProvider):
    def fetch_hourly(self, dt: date, lat: float, lon: float) -> list[HourlyWeather]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": dt.isoformat(),
            "end_date": dt.isoformat(),
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "wind_gusts_10m",
                "pressure_msl",
                "cloud_cover",
                "shortwave_radiation",
                "dew_point_2m",
                "apparent_temperature",
            ],
            "timezone": "UTC",
        }

        resp = requests.get(OPEN_METEO_BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        result: list[HourlyWeather] = []
        for i, t_str in enumerate(times):
            t = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
            result.append(
                HourlyWeather(
                    time=t,
                    temperature_2m=_safe_float(hourly, "temperature_2m", i),
                    relative_humidity_2m=_safe_float(hourly, "relative_humidity_2m", i),
                    wind_speed_10m=_safe_float(hourly, "wind_speed_10m", i),
                    wind_gusts_10m=_safe_float(hourly, "wind_gusts_10m", i),
                    pressure_msl=_safe_float(hourly, "pressure_msl", i),
                    cloud_cover=_safe_float(hourly, "cloud_cover", i),
                    shortwave_radiation=_safe_float(hourly, "shortwave_radiation", i),
                    dew_point_2m=_safe_float(hourly, "dew_point_2m", i),
                    apparent_temperature=_safe_float(hourly, "apparent_temperature", i),
                )
            )
        return result


def _safe_float(data: dict, key: str, idx: int) -> float | None:
    vals = data.get(key)
    if vals is None or idx >= len(vals) or vals[idx] is None:
        return None
    return float(vals[idx])
