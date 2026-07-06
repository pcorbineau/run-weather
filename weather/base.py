from abc import ABC, abstractmethod
from datetime import date

from models import HourlyWeather


class WeatherProvider(ABC):
    @abstractmethod
    def fetch_hourly(self, dt: date, lat: float, lon: float) -> list[HourlyWeather]:
        ...
