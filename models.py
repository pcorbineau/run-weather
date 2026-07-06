from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


@dataclass
class TrackPoint:
    time: datetime
    latitude: float
    longitude: float
    elevation: float | None = None
    heart_rate: float | None = None
    cadence: float | None = None
    power: float | None = None
    speed: float | None = None


@dataclass
class HourlyWeather:
    time: datetime
    temperature_2m: float
    relative_humidity_2m: float
    wind_speed_10m: float
    wind_gusts_10m: float | None = None
    pressure_msl: float | None = None
    cloud_cover: float | None = None
    shortwave_radiation: float | None = None
    dew_point_2m: float | None = None
    apparent_temperature: float | None = None


@dataclass
class ThermalMetrics:
    apparent_temperature: float | None = None
    felt_temperature: float | None = None
    heat_index: float | None = None
    wind_chill: float | None = None
    humidex: float | None = None
    wbgt: float | None = None


@dataclass
class EnhancedPoint:
    track: TrackPoint
    weather: HourlyWeather | None = None
    thermal: ThermalMetrics | None = None
    pace_min_km: float | None = None


@dataclass
class Activity:
    name: str
    sport_type: str
    start_time: datetime
    points: list[EnhancedPoint] = field(default_factory=list)

    @property
    def duration(self) -> float:
        if len(self.points) < 2:
            return 0.0
        return (self.points[-1].track.time - self.points[0].track.time).total_seconds()

    @property
    def distance_km(self) -> float:
        total = 0.0
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1].track
            p2 = self.points[i].track
            d = haversine(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
            total += d
        return total

    @property
    def elevation_gain(self) -> float:
        total = 0.0
        for i in range(1, len(self.points)):
            e1 = self.points[i - 1].track.elevation
            e2 = self.points[i].track.elevation
            if e1 is not None and e2 is not None and e2 > e1:
                total += e2 - e1
        return total

    @property
    def elevation_loss(self) -> float:
        total = 0.0
        for i in range(1, len(self.points)):
            e1 = self.points[i - 1].track.elevation
            e2 = self.points[i].track.elevation
            if e1 is not None and e2 is not None and e2 < e1:
                total += e1 - e2
        return total


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c
