import numpy as np

from models import EnhancedPoint, ThermalMetrics


def compute_thermal_metrics(ep: EnhancedPoint) -> ThermalMetrics:
    w = ep.weather
    if w is None:
        return ThermalMetrics()

    T = w.temperature_2m
    HR = w.relative_humidity_2m
    WS = w.wind_speed_10m

    apparent = w.apparent_temperature if w.apparent_temperature is not None else _apparent_temperature(T, HR, WS)
    hi = _heat_index(T, HR)
    wc = _wind_chill(T, WS)
    hx = _humidex(T, HR)
    wbgt_val = _wbgt_simple(T, HR)

    return ThermalMetrics(
        apparent_temperature=apparent,
        heat_index=hi,
        wind_chill=wc,
        humidex=hx,
        wbgt=wbgt_val,
    )


_vp = lambda T, HR: (HR / 100.0) * 6.105 * np.exp(17.27 * T / (237.7 + T))


def _apparent_temperature(T: float, HR: float, WS: float) -> float:
    e = _vp(T, HR)
    Ta = T + 0.33 * e - 0.70 * WS - 4.00
    return round(Ta, 1)


def _heat_index(T: float, HR: float) -> float | None:
    if T < 27 or HR < 40:
        return None
    hi = (
        -8.78469475556
        + 1.61139411 * T
        + 2.33854883889 * HR
        - 0.14611605 * T * HR
        - 0.012308094 * T**2
        - 0.0164248277778 * HR**2
        + 0.002211732 * T**2 * HR
        + 0.00072546 * T * HR**2
        - 0.000003582 * T**2 * HR**2
    )
    return round(hi, 1)


def _wind_chill(T: float, WS: float) -> float | None:
    if T > 10 or WS < 4.8:
        return None
    wc = 13.12 + 0.6215 * T - 11.37 * (WS * 3.6) ** 0.16 + 0.3965 * T * (WS * 3.6) ** 0.16
    return round(wc, 1)


def _humidex(T: float, HR: float) -> float:
    e = _vp(T, HR)
    hx = T + 0.5555 * (e - 10)
    return round(hx, 1)


def _wbgt_simple(T: float, HR: float) -> float:
    e = _vp(T, HR)
    wbgt = 0.567 * T + 0.393 * e + 3.94
    return round(wbgt, 1)


def compute_all_metrics(points: list[EnhancedPoint]) -> list[EnhancedPoint]:
    for ep in points:
        ep.thermal = compute_thermal_metrics(ep)
    return points


def compute_pace(points: list[EnhancedPoint]) -> list[EnhancedPoint]:
    for i in range(1, len(points)):
        p1 = points[i - 1].track
        p2 = points[i].track
        dt = (p2.time - p1.time).total_seconds()
        if dt <= 0:
            continue
        from models import haversine
        d = haversine(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
        if d > 0:
            points[i].pace_min_km = (dt / 60.0) / d
    return points
