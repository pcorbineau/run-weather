from datetime import date, datetime, timezone
from collections import defaultdict

import numpy as np

from models import Activity, HourlyWeather, TrackPoint, EnhancedPoint
from weather.base import WeatherProvider
from cache import WeatherCache


class WeatherService:
    def __init__(self, provider: WeatherProvider, cache: WeatherCache | None = None):
        self._provider = provider
        self._cache = cache or WeatherCache()

    def enrich(self, activity: Activity) -> Activity:
        points_by_date: dict[date, list[EnhancedPoint]] = defaultdict(list)
        for ep in activity.points:
            d = ep.track.time.date()
            points_by_date[d].append(ep)

        for day, pts in points_by_date.items():
            center_lat = np.mean([p.track.latitude for p in pts])
            center_lon = np.mean([p.track.longitude for p in pts])

            hourly = self._get_hourly(day, center_lat, center_lon)
            if not hourly:
                continue

            for ep in pts:
                weather = self._interpolate(hourly, ep.track.time)
                ep.weather = weather

        return activity

    def _get_hourly(self, day: date, lat: float, lon: float) -> list[HourlyWeather] | None:
        cached = self._cache.get(day, lat, lon)
        if cached is not None:
            result = []
            for d in cached:
                d["time"] = datetime.fromisoformat(d["time"])
                result.append(HourlyWeather(**d))
            return result

        try:
            data = self._provider.fetch_hourly(day, lat, lon)
            self._cache.set(day, lat, lon, [_asdict(h) for h in data])
            return data
        except Exception:
            return None

    def _interpolate(self, hourly: list[HourlyWeather], t: datetime) -> HourlyWeather | None:
        if not hourly:
            return None
        if len(hourly) == 1:
            return hourly[0]

        t_sec = t.timestamp()
        before, after = None, None
        for h in hourly:
            h_sec = h.time.timestamp()
            if h_sec <= t_sec:
                before = h
            if h_sec >= t_sec and after is None:
                after = h

        if before is None:
            return after
        if after is None:
            return before
        if before is after:
            return before

        b_sec = before.time.timestamp()
        a_sec = after.time.timestamp()
        if a_sec == b_sec:
            return before

        fraction = (t_sec - b_sec) / (a_sec - b_sec)

        def lerp(b_val, a_val):
            if b_val is None and a_val is None:
                return None
            if b_val is None:
                return a_val
            if a_val is None:
                return b_val
            return b_val + (a_val - b_val) * fraction

        return HourlyWeather(
            time=t,
            temperature_2m=lerp(before.temperature_2m, after.temperature_2m),
            relative_humidity_2m=lerp(before.relative_humidity_2m, after.relative_humidity_2m),
            wind_speed_10m=lerp(before.wind_speed_10m, after.wind_speed_10m),
            wind_gusts_10m=lerp(before.wind_gusts_10m, after.wind_gusts_10m),
            pressure_msl=lerp(before.pressure_msl, after.pressure_msl),
            cloud_cover=lerp(before.cloud_cover, after.cloud_cover),
            shortwave_radiation=lerp(before.shortwave_radiation, after.shortwave_radiation),
            dew_point_2m=lerp(before.dew_point_2m, after.dew_point_2m),
            apparent_temperature=lerp(before.apparent_temperature, after.apparent_temperature),
        )


def _asdict(h: HourlyWeather) -> dict:
    return {
        "time": h.time.isoformat(),
        "temperature_2m": h.temperature_2m,
        "relative_humidity_2m": h.relative_humidity_2m,
        "wind_speed_10m": h.wind_speed_10m,
        "wind_gusts_10m": h.wind_gusts_10m,
        "pressure_msl": h.pressure_msl,
        "cloud_cover": h.cloud_cover,
        "shortwave_radiation": h.shortwave_radiation,
        "dew_point_2m": h.dew_point_2m,
        "apparent_temperature": h.apparent_temperature,
    }
